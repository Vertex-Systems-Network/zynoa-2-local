# Actual Windows WebView2 keyboard/UI Automation probe, synthetic runner profile only.
param(
 [Parameter(Mandatory=$true)][string]$Executable,
 [Parameter(Mandatory=$true)][string]$SourceSha,
 [Parameter(Mandatory=$true)][string]$OutputDirectory,
 [switch]$ModelAcceptance,
 [switch]$AttachmentAcceptance,
 [switch]$PartialAcceptance,
 [string]$PriorModelProofDirectory=''
)
$ErrorActionPreference='Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $SourceSha -cnotmatch '^[a-f0-9]{40}$') { throw 'ZYN-CHAT-PROBE-001: disposable CI only' }
if ((git rev-parse HEAD).Trim() -cne $SourceSha) { throw 'ZYN-CHAT-PROBE-002: source mismatch' }
$expected=Join-Path $env:GITHUB_WORKSPACE 'apps\desktop\src-tauri\target\release\zynoa_desktop.exe'
if ([IO.Path]::GetFullPath($Executable) -ine [IO.Path]::GetFullPath($expected)) { throw 'ZYN-CHAT-PROBE-003: unexpected executable' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'ZYN-CHAT-PROBE-004: proof directory already exists' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ChatProbeWindow {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hwnd, int command);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
 [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr hwnd, uint flags);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);

 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
 [DllImport("user32.dll")] private static extern bool EnumChildWindows(IntPtr parent, EnumChildCallback callback, IntPtr data);
 private delegate bool EnumChildCallback(IntPtr child, IntPtr data);
 [DllImport("user32.dll")] private static extern int GetDlgCtrlID(IntPtr hwnd);
 [DllImport("user32.dll")] private static extern IntPtr GetParent(IntPtr hwnd);
 [DllImport("user32.dll")] public static extern bool IsChild(IntPtr parent, IntPtr child);
 [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hwnd);
 [DllImport("user32.dll")] private static extern bool IsWindowEnabled(IntPtr hwnd);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] private static extern int GetClassName(IntPtr hwnd, System.Text.StringBuilder text, int count);
 [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint process);
 [DllImport("user32.dll")] private static extern bool GetGUIThreadInfo(uint thread, ref GUITHREADINFO info);
 [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
 private static extern IntPtr SendMessageTimeout(IntPtr hwnd, uint msg, UIntPtr wParam, System.Text.StringBuilder text, uint flags, uint timeout, out UIntPtr result);
 [StructLayout(LayoutKind.Sequential)] private struct GUITHREADINFO {
   public uint cbSize, flags; public IntPtr active, focus, capture, menuOwner, moveSize, caret; public RECT caretRect;
 }
 private static string ClassOf(IntPtr h) {
   var text = new System.Text.StringBuilder(128); GetClassName(h,text,text.Capacity); return text.ToString();
 }
 public static IntPtr[] FilenameEdits(IntPtr dialog) {
   var result = new System.Collections.Generic.List<IntPtr>();
   EnumChildWindows(dialog, delegate(IntPtr child, IntPtr ignored) {
     if (!String.Equals(ClassOf(child),"Edit",StringComparison.OrdinalIgnoreCase) ||
         !IsWindowVisible(child) || !IsWindowEnabled(child)) return true;
     bool anchored = GetDlgCtrlID(child)==1152;
     for (IntPtr parent=GetParent(child); parent!=IntPtr.Zero && parent!=dialog && IsChild(dialog,parent); parent=GetParent(parent)) {
       string cls=ClassOf(parent);
       if (GetDlgCtrlID(parent)==1148 && (cls=="ComboBoxEx32" || cls=="ComboBox")) anchored=true;
     }
     if (anchored) result.Add(child);
     return true;
   }, IntPtr.Zero);
   return result.ToArray();
 }
 public static string[] ChildInventory(IntPtr dialog) {
   var result=new System.Collections.Generic.List<string>();
   EnumChildWindows(dialog, delegate(IntPtr child, IntPtr ignored) {
     if (result.Count>=256) return false;
     IntPtr parent=GetParent(child);
     result.Add("class="+ClassOf(child)+" id="+GetDlgCtrlID(child)+" parent_class="+ClassOf(parent)+" parent_id="+GetDlgCtrlID(parent)+" visible="+IsWindowVisible(child)+" enabled="+IsWindowEnabled(child));
     return true;
   },IntPtr.Zero);
   return result.ToArray();
 }
 public static bool OwnsKeyboardFocus(IntPtr dialog, IntPtr child) {
   uint process; uint thread=GetWindowThreadProcessId(dialog,out process);
   var info=new GUITHREADINFO(); info.cbSize=(uint)Marshal.SizeOf(typeof(GUITHREADINFO));
   return thread!=0 && GetGUIThreadInfo(thread,ref info) && info.focus==child && IsChild(dialog,child);
 }
 public static string ReadEditText(IntPtr dialog, IntPtr child) {
   if (!IsChild(dialog,child) || !OwnsKeyboardFocus(dialog,child) || ClassOf(child)!="Edit") throw new InvalidOperationException("Unverified dialog edit");
   var buffer=new System.Text.StringBuilder(32768); UIntPtr result;
   if (SendMessageTimeout(child,0x000D,(UIntPtr)(uint)buffer.Capacity,buffer,2,2000,out result)==IntPtr.Zero)
     throw new InvalidOperationException("Filename readback unavailable");
   return buffer.ToString();
 }
 [StructLayout(LayoutKind.Sequential)] public struct RECT {public int Left,Top,Right,Bottom;}
}
'@
$script:app=$null
$script:root=$null
$script:hwnd=[IntPtr]::Zero
$script:stage='initializing'
$script:inputChecks=[System.Collections.Generic.List[object]]::new()
$title='P03 synthetic conversation'
$content='P03 synthetic persisted message'
function Start-Native {
 $script:app=Start-Process -FilePath $Executable -PassThru
 for ($i=0;$i -lt 90;$i++) {
   Start-Sleep -Milliseconds 500
   $script:app.Refresh()
   if ($script:app.HasExited) { throw 'ZYN-CHAT-PROBE-005: native process exited' }
   if ($script:app.MainWindowHandle -ne [IntPtr]::Zero) {break}
 }
 $script:hwnd=$script:app.MainWindowHandle
 if ($script:hwnd -eq [IntPtr]::Zero) {throw 'ZYN-CHAT-PROBE-006: window missing'}
 [void][ChatProbeWindow]::ShowWindow($script:hwnd,3)
 [void][ChatProbeWindow]::SetForegroundWindow($script:hwnd)
 $script:root=[System.Windows.Automation.AutomationElement]::FromHandle($script:hwnd)
 if ($null -eq $script:root -or $script:root.Current.ProcessId -ne $script:app.Id) {throw 'ZYN-CHAT-PROBE-007: HWND/PID mismatch'}
}
function Stop-Native {
 if ($null -ne $script:app) {
   $script:app.Refresh()
   if (!$script:app.HasExited) {
     [void]$script:app.CloseMainWindow()
     if (!$script:app.WaitForExit(10000)) {Stop-Process -Id $script:app.Id -Force; $script:app.WaitForExit()}
   }
 }
 $script:root=$null
}
function Wait-Name([string]$Name,[string]$Type='', [bool]$Enabled=$false,[int]$Attempts=80) {
 $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$Name)
 for ($i=0;$i -lt $Attempts;$i++) {
   $matches=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
   for ($j=0;$j -lt $matches.Count;$j++) {
     try {
       $e=$matches.Item($j)
       if ($Type -and $e.Current.ControlType.ProgrammaticName -ne ('ControlType.'+$Type)) {continue}
       if ($Enabled -and !$e.Current.IsEnabled) {continue}
       # Completion status remains above the composer after Send scrolls it
       # into view. Read its exact accessible text even outside the viewport;
       # the later independent vault checks still verify durable output.
       if (!$e.Current.IsOffscreen -or $Type -or $Name -ceq 'Turn stopped; any partial response was saved as cancelled.' -or $Name -ceq 'Local model response completed and saved.' -or $Name -ceq 'Message and attachments saved locally. No model response was requested.') {return $e}
     } catch [System.Windows.Automation.ElementNotAvailableException] {}
   }
   Start-Sleep -Milliseconds 250
 }
 throw ('ZYN-CHAT-PROBE-008: required UI control missing: '+$Name)
}
function Focus-Control($Control) {
 $pattern=$null
 if ($Control.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$pattern)) {$pattern.ScrollIntoView()}
 [void][ChatProbeWindow]::SetForegroundWindow($script:hwnd)
 if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-CHAT-PROBE-009: foreground mismatch'}
 $Control.SetFocus()
 Start-Sleep -Milliseconds 350
}
function Click-Control([string]$Name) {
 $control=Wait-Name $Name 'Button' $true
 Focus-Control $control
 # ARIA pressed buttons may expose TogglePattern rather than InvokePattern.
 # Select the actual supported provider pattern, never assume ControlType.Button
 # implies InvokePattern. A physical click is bounded to the native HWND.
 $pattern=$null
 if ($control.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)) {
   $pattern.Invoke()
   Write-Output ('Native activation: '+$Name+' via InvokePattern')
 } else {
   $pattern=$null
   if ($control.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$pattern)) {
     $pattern.Toggle()
     Write-Output ('Native activation: '+$Name+' via TogglePattern')
   } else {
     Focus-ByPhysicalClick $control
     Write-Output ('Native activation: '+$Name+' via physical click')
   }
 }
}
function Focus-ByPhysicalClick($Control) {
 Focus-Control $Control
 $point=$Control.GetClickablePoint()
 $rect=New-Object ChatProbeWindow+RECT
 if (![ChatProbeWindow]::GetWindowRect($script:hwnd,[ref]$rect)) {throw 'ZYN-CHAT-PROBE-017: click bounds unavailable'}
 $x=[int]$point.X;$y=[int]$point.Y
 if ($x -lt $rect.Left -or $x -ge $rect.Right -or $y -lt $rect.Top -or $y -ge $rect.Bottom) {throw 'ZYN-CHAT-PROBE-018: click outside native HWND'}
 if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-CHAT-PROBE-019: foreground lost before click'}
 if (![ChatProbeWindow]::SetCursorPos($x,$y)) {throw 'ZYN-CHAT-PROBE-020: native pointer positioning failed'}
 [ChatProbeWindow]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 [ChatProbeWindow]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 350
}
function Type-Exact([string]$Name,[string]$Text) {
 $script:stage='keyboard '+$Name
 for ($attempt=1;$attempt -le 2;$attempt++) {
   $control=Wait-Name $Name 'Edit' $true
   if ($attempt -eq 1) {Focus-Control $control} else {Focus-ByPhysicalClick $control}
   if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-CHAT-PROBE-021: foreground lost before input'}
   $focused=[System.Windows.Automation.AutomationElement]::FocusedElement
   $focusMatches=$null -ne $focused -and $focused.Current.Name -ceq $Name -and $focused.Current.ControlType.ProgrammaticName -eq 'ControlType.Edit'
   # Only synthetic text. No clipboard, ValuePattern.SetValue, JS, or database write.
   # Clear previous partial input with keyboard, then type at a bounded pace.
   [System.Windows.Forms.SendKeys]::SendWait('^a')
   [System.Windows.Forms.SendKeys]::SendWait('{BACKSPACE}')
   foreach ($char in $Text.ToCharArray()) {
     [System.Windows.Forms.SendKeys]::SendWait([string]$char)
     Start-Sleep -Milliseconds 50
   }
   $observedLength=-1
   $exact=$false
   for ($i=0;$i -lt 20;$i++) {
     $control=Wait-Name $Name 'Edit' $true
     $value=$control.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
     $observed=[string]$value.Current.Value
     $observedLength=$observed.Length
     if ($observed -ceq $Text) {$exact=$true;break}
     Start-Sleep -Milliseconds 250
   }
   $check=[ordered]@{control=$Name;attempt=$attempt;focus_name_and_type_match=[bool]$focusMatches;observed_length=$observedLength;expected_length=$Text.Length;exact_keyboard_readback=[bool]$exact;method=if($attempt -eq 1){'UIA focus + paced keyboard'}else{'physical click + paced keyboard'}}
   $script:inputChecks.Add($check)
   Write-Output ('Native keyboard check: '+($check | ConvertTo-Json -Compress))
   if ($exact) {return}
 }
 throw ('ZYN-CHAT-PROBE-010: keyboard input not reflected by actual UIA value: '+$Name)
}
function Capture([string]$Name) {
 [void][ChatProbeWindow]::SetForegroundWindow($script:hwnd)
 Start-Sleep -Milliseconds 400
 if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-CHAT-PROBE-011: screenshot foreground mismatch'}
 $rect=New-Object ChatProbeWindow+RECT
 if (![ChatProbeWindow]::GetWindowRect($script:hwnd,[ref]$rect)) {throw 'ZYN-CHAT-PROBE-012: window rect unavailable'}
 $screen=[System.Windows.Forms.SystemInformation]::VirtualScreen
 $x=[Math]::Max($screen.Left,$rect.Left);$y=[Math]::Max($screen.Top,$rect.Top)
 $w=[Math]::Min($screen.Right,$rect.Right)-$x;$h=[Math]::Min($screen.Bottom,$rect.Bottom)-$y
 if ($w -lt 800 -or $h -lt 500) {throw 'ZYN-CHAT-PROBE-013: capture too small'}
 $bitmap=[System.Drawing.Bitmap]::new($w,$h)
 try {
   $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
   try {$graphics.CopyFromScreen($x,$y,0,0,$bitmap.Size)} finally {$graphics.Dispose()}
   $colors=[System.Collections.Generic.HashSet[int]]::new()
   for ($ix=0;$ix -lt 20;$ix++) {for ($iy=0;$iy -lt 15;$iy++) {[void]$colors.Add($bitmap.GetPixel([int](($w-1)*$ix/20),[int](($h-1)*$iy/15)).ToArgb())}}
   if ($colors.Count -lt 6) {throw 'ZYN-CHAT-PROBE-014: blank capture'}
   $path=Join-Path $OutputDirectory $Name
   $bitmap.Save($path,[System.Drawing.Imaging.ImageFormat]::Png)
 } finally {$bitmap.Dispose()}
}
function Read-Vault([string]$Stage) {
 $env:ZYNOA_CHAT_PROOF_STAGE=$Stage
 $env:ZYNOA_CHAT_PROOF_DIR=$OutputDirectory
 python scripts/verify_p03_chat_ui_database.py
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-CHAT-PROBE-015: independent SQLite verification failed'}
}
function Read-ModelVault([string]$Stage,[string]$Title='',[string]$Model='',[int]$Budget=0) {
 $result = & python scripts/verify_p03_model_ui_database.py --stage $Stage --output $OutputDirectory --title $Title --model $Model --budget $Budget
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-MODEL-PROBE-001: independent SQLite verification failed'}
 return ($result | ConvertFrom-Json)
}
function Test-Combo([string]$Name,[string]$Expected) {
 $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$Name)
 $matches=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
 foreach ($control in $matches) {
   try {
     if ($control.Current.ControlType.ProgrammaticName -ne 'ControlType.ComboBox' -or !$control.Current.IsEnabled) {continue}
     $value=$null
     if ($control.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$value)) {
       if ([string]$value.Current.Value -ceq $Expected) {return $true}
     }
     $selection=$null
     if ($control.TryGetCurrentPattern([System.Windows.Automation.SelectionPattern]::Pattern,[ref]$selection)) {
       foreach ($item in $selection.Current.GetSelection()) {
         if ($item.Current.Name -ceq $Expected) {return $true}
       }
     }
   } catch [System.Windows.Automation.ElementNotAvailableException] {}
 }
 return $false
}
function Assert-Combo([string]$Name,[string]$Expected) {
 for ($i=0;$i -lt 40;$i++) {
   if (Test-Combo $Name $Expected) {return}
   Start-Sleep -Milliseconds 250
 }
 throw ('ZYN-MODEL-PROBE-003: exact model/context dropdown readback failed: '+$Name)
}
function Select-Combo([string]$Name,[string]$Key,[string]$Expected) {
 # Selection is accepted only when the enabled native control reads back
 # the exact requested option. React sets this value after the native reply.
 if (Test-Combo $Name $Expected) {return}
 for ($attempt=1;$attempt -le 2;$attempt++) {
   $control=Wait-Name $Name 'ComboBox' $true
   $method='physical click + keyboard'
   if ($attempt -eq 1) {
     # Prefer the real provider's item selection when it is available.
     # Expand the native dropdown; scope all UIA search to the actual HWND.
     Focus-Control $control
     $expand=$null
     $selected=$false
     if ($control.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$expand)) {
       try {
         $expand.Expand()
         Start-Sleep -Milliseconds 200
         $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$Expected)
         $items=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
         foreach ($item in $items) {
           if ($item.Current.IsOffscreen -or !$item.Current.IsEnabled) {continue}
           $kind=$item.Current.ControlType.ProgrammaticName
           if ($kind -notin @('ControlType.ListItem','ControlType.DataItem')) {continue}
           $selection=$null
           if ($item.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$selection)) {
             $selection.Select()
             $selected=$true
             $method='native UIA SelectionItem'
             break
           }
         }
       } catch {Write-Output 'Native dropdown item pattern unavailable; use physical keyboard path'}
       finally {try {$expand.Collapse()} catch {}}
     }
     if ($selected) {
       for ($i=0;$i -lt 40;$i++) {
         if (Test-Combo $Name $Expected) {
           Write-Output ('Native dropdown exact readback: '+$Name+' / '+$Expected+' via '+$method)
           return
         }
         Start-Sleep -Milliseconds 250
       }
       continue
     }
   }
   # Real focus + click (the prior title keyboard proof required this).
   # The second attempt selects by the first character for the first model:
   # Home may stay on the disabled placeholder on some WebView2 providers.
   $control=Wait-Name $Name 'ComboBox' $true
   Focus-ByPhysicalClick $control
   # WebView2 can expose the popup option without a SelectionItemPattern.
   # On that provider, click the exact visible option before keyboard fallback.
   if ($attempt -eq 2) {
     $expand=$null
     if ($control.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$expand)) {
       try {
         $expand.Expand(); Start-Sleep -Milliseconds 200
         $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$Expected)
         $items=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
         foreach ($item in $items) {
           if ($item.Current.IsOffscreen -or !$item.Current.IsEnabled) {continue}
           try { Focus-ByPhysicalClick $item; [System.Windows.Forms.SendKeys]::SendWait('{ENTER}'); break } catch {}
         }
       } catch {} finally {try {$expand.Collapse()} catch {}}
       for ($i=0;$i -lt 40;$i++) { if (Test-Combo $Name $Expected) { return }; Start-Sleep -Milliseconds 250 }
     }
   }
   if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-MODEL-PROBE-002: foreground lost'}
   $actualKey=$Key
   # The model selector keeps a disabled placeholder at index zero on some
   # WebView2 builds. HOME alone therefore never reaches the first installed
   # model; move one bounded step past the placeholder before committing.
   if ($attempt -eq 2 -and $Name -ceq 'Model') {
     # WebView2 can ignore HOME/DOWN while the placeholder remains selected.
     # Type the exact visible option so native select type-ahead resolves it;
     # acceptance still requires exact UIA readback below.
     [System.Windows.Forms.SendKeys]::SendWait($Expected)
   } else {
     [System.Windows.Forms.SendKeys]::SendWait($actualKey)
   }
   [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
   for ($i=0;$i -lt 40;$i++) {
     if (Test-Combo $Name $Expected) {
       Write-Output ('Native dropdown exact readback: '+$Name+' / '+$Expected+' via '+$method+' attempt '+$attempt)
       return
     }
     Start-Sleep -Milliseconds 250
   }
   if ([ChatProbeWindow]::GetForegroundWindow() -eq $script:hwnd) {[System.Windows.Forms.SendKeys]::SendWait('{ESC}')}
 }
 throw ('ZYN-MODEL-PROBE-003: actual dropdown selection not acknowledged: '+$Name+' / '+$Expected)
}
function Wait-TextPattern([string]$Pattern,[int]$Attempts=80) {
 for ($i=0;$i -lt $Attempts;$i++) {
   $items=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
   foreach ($item in $items) {
     try {
       $name=[string]$item.Current.Name
       if ($name -match $Pattern -and !$item.Current.IsOffscreen) {return $name}
     } catch [System.Windows.Automation.ElementNotAvailableException] {}
   }
   Start-Sleep -Milliseconds 250
 }
 throw 'ZYN-MODEL-PROBE-004: required accessible text absent'
}
function Wait-Assistant([string]$Text) {
 $normalized=($Text -replace '\s+',' ').Trim()
 if (!$normalized) {throw 'ZYN-MODEL-PROBE-005: empty assistant output'}
 for ($i=0;$i -lt 80;$i++) {
   $items=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
   foreach ($item in $items) {
     try {
       if (([string]$item.Current.Name -replace '\s+',' ').Trim() -ceq $normalized) {
         if (!$item.Current.IsOffscreen) {return}
         $scrollItem=$null
         if ($item.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$scrollItem)) {
           $scrollItem.ScrollIntoView()
         } else {
           $item.SetFocus()
         }
       }
     } catch [System.Windows.Automation.ElementNotAvailableException] {}
   }
   Start-Sleep -Milliseconds 250
 }
 throw 'ZYN-MODEL-PROBE-006: persisted assistant text not visible in native UI'
}

function Read-AttachmentVault([string]$Stage) {
 & python scripts/verify_p03_attachment_ui_database.py --stage $Stage --output $OutputDirectory
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-ATTACH-PROBE-001: independent database/blob verification failed'}
}
function Select-SyntheticFile([string]$Path) {
 # Use only the actual OS file dialog, never JS, DOM injection or native IPC.
 if ($Path -cnotmatch '^[A-Za-z0-9_:\\ .-]+$') {throw 'ZYN-ATTACH-PROBE-002: unexpected fixture path'}
 $button=Wait-Name 'Attach local files' 'Button' $true
 Focus-ByPhysicalClick $button
 $dialog=[IntPtr]::Zero
 for ($i=0;$i -lt 80;$i++) {
   $candidate=[ChatProbeWindow]::GetForegroundWindow()
   if ($candidate -ne [IntPtr]::Zero -and $candidate -ne $script:hwnd) {
     $element=[System.Windows.Automation.AutomationElement]::FromHandle($candidate)
     if ($null -ne $element -and $element.Current.ClassName -eq '#32770') {
       $owner=[ChatProbeWindow]::GetAncestor($candidate,3)
       if ($owner -eq $script:hwnd -or $element.Current.ProcessId -eq $script:app.Id) {$dialog=$candidate;break}
       # WebView2 may own the dialog in a child process; verify ancestry.
       $pidToCheck=$element.Current.ProcessId
       for ($depth=0;$depth -lt 12 -and $pidToCheck -gt 0;$depth++) {
         if ($pidToCheck -eq $script:app.Id) {$dialog=$candidate;break}
         $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$pidToCheck"
         if (!$proc -or $proc.ParentProcessId -eq $pidToCheck) {break}
         $pidToCheck=$proc.ParentProcessId
       }
       if ($dialog -ne [IntPtr]::Zero) {break}
     }
   }
   Start-Sleep -Milliseconds 250
 }
 if ($dialog -eq [IntPtr]::Zero) {throw 'ZYN-ATTACH-PROBE-003: owned native file dialog missing'}
 # Native common-dialog control IDs: cmb13 (1148) / edt1 (1152).
 # UIA provider did not expose a unique labeled Edit on the last run.
 # Enumerate real child HWNDs only within the already verified owned dialog.
 $filenameEdit=[IntPtr]::Zero
 for ($attempt=0;$attempt -lt 40;$attempt++) {
   if ([ChatProbeWindow]::GetForegroundWindow() -ne $dialog) {throw 'ZYN-ATTACH-PROBE-004: dialog foreground lost'}
   $matches=@([ChatProbeWindow]::FilenameEdits($dialog))
   if ($matches.Count -eq 1) {$filenameEdit=$matches[0];break}
   Start-Sleep -Milliseconds 250
 }
 if ($filenameEdit -eq [IntPtr]::Zero) {
   [ChatProbeWindow]::ChildInventory($dialog) | Set-Content -LiteralPath (Join-Path $OutputDirectory 'dialog-control-inventory.txt') -Encoding utf8
   throw 'ZYN-ATTACH-PROBE-005: unique native filename edit not found'
 }
 $rect=New-Object ChatProbeWindow+RECT
 $bounds=New-Object ChatProbeWindow+RECT
 if (![ChatProbeWindow]::GetWindowRect($dialog,[ref]$rect) -or ![ChatProbeWindow]::GetWindowRect($filenameEdit,[ref]$bounds)) {throw 'ZYN-ATTACH-PROBE-005: dialog or filename bounds unavailable'}
 if ($bounds.Right-$bounds.Left -lt 10 -or $bounds.Bottom-$bounds.Top -lt 5) {throw 'ZYN-ATTACH-PROBE-005: filename edit bounds invalid'}
 $x=[int](($bounds.Left+$bounds.Right)/2);$y=[int](($bounds.Top+$bounds.Bottom)/2)
 if ($x -lt $rect.Left -or $x -ge $rect.Right -or $y -lt $rect.Top -or $y -ge $rect.Bottom -or [ChatProbeWindow]::GetForegroundWindow() -ne $dialog -or ![ChatProbeWindow]::IsChild($dialog,$filenameEdit)) {throw 'ZYN-ATTACH-PROBE-005: filename click not inside owned foreground dialog'}
 if (![ChatProbeWindow]::SetCursorPos($x,$y)) {throw 'ZYN-ATTACH-PROBE-005: pointer positioning failed'}
 [ChatProbeWindow]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 [ChatProbeWindow]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
 for ($i=0;$i -lt 20;$i++) {
   if ([ChatProbeWindow]::OwnsKeyboardFocus($dialog,$filenameEdit)) {break}
   Start-Sleep -Milliseconds 100
 }
 if (![ChatProbeWindow]::OwnsKeyboardFocus($dialog,$filenameEdit) -or [ChatProbeWindow]::GetForegroundWindow() -ne $dialog) {
   [ChatProbeWindow]::ChildInventory($dialog) | Set-Content -LiteralPath (Join-Path $OutputDirectory 'dialog-control-inventory.txt') -Encoding utf8
   throw 'ZYN-ATTACH-PROBE-005: exact native filename edit not focused'
 }
 [System.Windows.Forms.SendKeys]::SendWait('^a')
 [System.Windows.Forms.SendKeys]::SendWait($Path)
 if ([ChatProbeWindow]::ReadEditText($dialog,$filenameEdit) -cne $Path) {throw 'ZYN-ATTACH-PROBE-006: file path keyboard readback mismatch'}
 Write-Output 'Native owned file dialog: exact HWND filename keyboard readback verified'
 if ([ChatProbeWindow]::GetForegroundWindow() -ne $dialog) {throw 'ZYN-ATTACH-PROBE-007: dialog foreground lost before confirmation'}
 [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
 [void](Wait-Name 'Remove p03-attachment-fixture.bin' 'Button' $true)
}
function Wait-SavedAttachment([string]$Name,[long]$Bytes) {
 $expected='Saved attachment: '+$Name+', '+$Bytes+' bytes'
 $visible=$Name+' ('+$Bytes.ToString('N0',[Globalization.CultureInfo]::GetCultureInfo('en-US'))+' bytes · stored metadata)'
 $historyCondition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'Saved messages')
 for ($attempt=0;$attempt -lt 80;$attempt++) {
   $histories=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$historyCondition)
   foreach ($history in $histories) {
     $items=$history.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
     foreach ($item in $items) {
       try {
         $name=([string]$item.Current.Name -replace '\s+',' ').Trim()
         if ($name -cne $expected -and $name -cne $visible) {continue}
         if (!$item.Current.IsOffscreen) {Write-Output 'Native saved attachment: exact filename and byte count read back in saved history';return}
         $scroll=$null
         if ($item.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$scroll)) {$scroll.ScrollIntoView()}
       } catch [System.Windows.Automation.ElementNotAvailableException] {}
     }
   }
   Start-Sleep -Milliseconds 250
 }
 # Preserve provider names/types from synthetic saved history, not real user data.
 $names=[System.Collections.Generic.List[object]]::new()
 foreach ($history in $script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$historyCondition)) {
   foreach ($item in $history.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)) {
     try {
       if ($names.Count -lt 100) {$names.Add([ordered]@{name=$item.Current.Name;type=$item.Current.ControlType.ProgrammaticName;offscreen=$item.Current.IsOffscreen})}
     } catch [System.Windows.Automation.ElementNotAvailableException] {}
   }
 }
 ConvertTo-Json -InputObject @($names.ToArray()) -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'synthetic-saved-history-uia.json') -Encoding utf8
 throw 'ZYN-ATTACH-PROBE-013: exact saved attachment filename and byte count not visible in history'
}
if ($AttachmentAcceptance) {
 try {
   if ($ModelAcceptance) {throw 'ZYN-ATTACH-PROBE-008: mutually exclusive journeys'}
   $script:stage='attachment baseline identity'
   Read-AttachmentVault 'baseline'
   $fixture=Join-Path $env:RUNNER_TEMP 'p03-attachment-fixture.bin'
   if (Test-Path -LiteralPath $fixture) {throw 'ZYN-ATTACH-PROBE-009: fixture already exists'}
   $bytes=[byte[]]::new(70000)
   for ($i=0;$i -lt $bytes.Length;$i++) {$bytes[$i]=[byte]($i % 251)}
   [IO.File]::WriteAllBytes($fixture,$bytes)
   $script:stage='attachment native first start'
   Start-Native
   $firstPid=$script:app.Id
   Click-Control 'Chat'
   Type-Exact 'Conversation title' 'P03 attachment proof'
   Click-Control 'Create conversation'
   [void](Wait-Name 'Message' 'Edit' $true)
   Type-Exact 'Message' 'P03 synthetic attachment message'
   $script:stage='select actual file'
   Select-SyntheticFile $fixture
   $remove=Wait-Name 'Remove p03-attachment-fixture.bin' 'Button' $true
   Focus-Control $remove
   Capture 'M03-S03-candidate.png'
   $script:stage='remove and reselect actual file'
   Click-Control 'Remove p03-attachment-fixture.bin'
   $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'Remove p03-attachment-fixture.bin')
   for ($i=0;$i -lt 40;$i++) {
     if ($script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition).Count -eq 0) {break}
     Start-Sleep -Milliseconds 250
   }
   if ($script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition).Count -ne 0) {throw 'ZYN-ATTACH-PROBE-010: removed file remains selected'}
   Select-SyntheticFile $fixture
   $script:stage='save attachment transaction'
   Click-Control 'Save message'
   [void](Wait-Name 'Message and attachments saved locally. No model response was requested.' '' $false 240)
   Stop-Native
   Read-AttachmentVault 'saved'
   # Remove only the disposable original fixture; verify independent managed storage.
   Remove-Item -LiteralPath $fixture
   if (Test-Path -LiteralPath $fixture) {throw 'ZYN-ATTACH-PROBE-011: original fixture remains'}
   $script:stage='restart and reopen saved attachment'
   Start-Native
   $secondPid=$script:app.Id
   if ($firstPid -eq $secondPid) {throw 'ZYN-ATTACH-PROBE-012: distinct process required'}
   Click-Control 'Chat'
   Click-Control 'P03 attachment proof'
   $script:stage='reopened message UI readback'
   Wait-Assistant 'P03 synthetic attachment message'
   $script:stage='reopened attachment filename and size UI readback'
   Wait-SavedAttachment 'p03-attachment-fixture.bin' 70000
   Capture 'M03-OPT-04-candidate.png'
   Stop-Native
   $script:stage='independent reopened attachment database and blob proof'
   Read-AttachmentVault 'reopened'
   $images=[ordered]@{}
   foreach ($name in @('M03-S03-candidate.png','M03-OPT-04-candidate.png')) {
     $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();first_pid=$firstPid;reopened_pid=$secondPid;synthetic_only=$true;actual_os_picker=$true;remove_reselect=$true;original_removed=$true;database_blob_reopen_verified=$true;ui_filename_readback=$true;input_checks=@($script:inputChecks.ToArray());images=$images;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false;model_ingestion_claimed=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-attachment-ui-proof.json') -Encoding utf8
 } catch {
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;stage=$script:stage;status='FAILED_NOT_ACCEPTANCE';synthetic_only=$true;input_checks=@($script:inputChecks.ToArray())} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-attachment-ui-failure.json') -Encoding utf8
   if ($script:hwnd -ne [IntPtr]::Zero -and $null -ne $script:root) {try {Capture 'DEBUG-native-attachment-ui-failure.png'} catch {Write-Output 'Failure screenshot unavailable'}}
   throw
 } finally {Stop-Native}
 return
}

function Read-PartialVault([string]$Stage) {
 $result=& python scripts/verify_p03_partial_ui_database.py --stage $Stage --output $OutputDirectory --prior $PriorModelProofDirectory
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-PARTIAL-PROBE-001: independent partial database verification failed'}
 return ($result | ConvertFrom-Json)
}
function Wait-RealStreamingPrefix {
 $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'Streaming assistant response')
 for ($i=0;$i -lt 1200;$i++) {
   $groups=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
   foreach ($group in $groups) {
     $textCondition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Text)
     foreach ($item in $group.FindAll([System.Windows.Automation.TreeScope]::Descendants,$textCondition)) {
       try {
         $prefix=([string]$item.Current.Name -replace '\s+',' ').Trim()
         if ($prefix.Length -ge 12 -and $prefix -cne 'Generating locally' -and $prefix -cne 'Streaming assistant response' -and !$item.Current.IsOffscreen) {return $prefix}
       } catch [System.Windows.Automation.ElementNotAvailableException] {}
     }
   }
   Start-Sleep -Milliseconds 100
 }
 throw 'ZYN-PARTIAL-PROBE-002: nonempty real streaming text not observed before Stop'
}
if ($PartialAcceptance) {
 try {
   if ($ModelAcceptance -or $AttachmentAcceptance -or !$PriorModelProofDirectory) {throw 'ZYN-PARTIAL-PROBE-003: separate journey requires prior model proof'}
   $script:stage='partial baseline identity'
   $null=Read-PartialVault 'baseline'
   $script:stage='native partial first start'
   Start-Native
   $firstPid=$script:app.Id
   Click-Control 'Chat'
   Type-Exact 'Conversation title' 'P03 partial persistence'
   Click-Control 'Create conversation'
   [void](Wait-Name 'Message' 'Edit' $true)
   Click-Control 'Refresh local models'
   Select-Combo 'Model' '{END}' 'qwen2.5:1.5b'
   Select-Combo 'Context budget' '{HOME}{DOWN 4}' '8192 tokens'
   Assert-Combo 'Model' 'qwen2.5:1.5b'
   Assert-Combo 'Context budget' '8192 tokens'
   Type-Exact 'Message' 'List the numbers from one to one thousand in words. Use one line for every number. Do not summarize or stop early.'
   $script:stage='actual real model stream'
   Click-Control 'Send'
   $prefix=Wait-RealStreamingPrefix
   $script:stage='actual Stop during nonempty stream'
   $stop=Wait-Name 'Stop' 'Button' $true 8
   if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-PARTIAL-PROBE-004: foreground lost before Stop'}
   $pattern=$null
   if (!$stop.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)) {throw 'ZYN-PARTIAL-PROBE-005: actual Stop activation unavailable'}
   $clock=[Diagnostics.Stopwatch]::StartNew()
   $pattern.Invoke()
   [void](Wait-Name 'Turn stopped; any partial response was saved as cancelled.' '' $false 80)
   $elapsed=[int64]$clock.ElapsedMilliseconds
   $script:stage='independent cancelled partial persistence'
   $saved=Read-PartialVault 'saved'
   $normalized=([string]$saved.assistant_text -replace '\s+',' ').Trim()
   if (!$normalized.StartsWith($prefix,[StringComparison]::Ordinal)) {throw 'ZYN-PARTIAL-PROBE-006: observed live prefix not present in durable cancelled response'}
   Wait-Assistant $saved.assistant_text
   Capture 'M03-OPT-02-stopped-candidate.png'
   Stop-Native
   $script:stage='reopen cancelled partial in distinct process'
   Start-Native
   $secondPid=$script:app.Id
   if ($firstPid -eq $secondPid) {throw 'ZYN-PARTIAL-PROBE-007: distinct process required'}
   Click-Control 'Chat'
   Click-Control 'P03 partial persistence'
   Wait-Assistant $saved.assistant_text
   Capture 'M03-OPT-02-partial-reopened-candidate.png'
   Stop-Native
   $script:stage='independent reopened partial identity'
   $null=Read-PartialVault 'reopened'
   $images=[ordered]@{}
   foreach ($name in @('M03-OPT-02-stopped-candidate.png','M03-OPT-02-partial-reopened-candidate.png')) {
     $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();first_pid=$firstPid;reopened_pid=$secondPid;synthetic_only=$true;actual_model='qwen2.5:1.5b';context_limit=8192;actual_native_stop=$true;nonempty_live_prefix_verified=$true;live_prefix_chars=$prefix.Length;stop_to_cancel_notice_ms=$elapsed;cancelled_partial_persisted=$true;ui_partial_reopen_verified=$true;database_reopen_identity_verified=$true;images=$images;visual_review='candidate_pending_visual_review';retry_ui_verified=$false;full_accessibility_certified=$false;input_checks=@($script:inputChecks.ToArray())} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-partial-ui-proof.json') -Encoding utf8
   Write-Output 'P03 T05 actual real-model partial response Stop and restart proof passed'
   $script:stage='retry baseline after independent partial reopen'
   $null=Read-PartialVault 'retry-baseline'
   Start-Native
   $retryPid=$script:app.Id
   if ($retryPid -eq $firstPid -or $retryPid -eq $secondPid) {throw 'ZYN-RETRY-PROBE-001: distinct process required'}
   Click-Control 'Chat'
   Click-Control 'P03 partial persistence'
   [void](Wait-Name 'Retry turn' 'Button' $true)
   Wait-Assistant $saved.assistant_text
   $script:stage='retry after restart with bounded response budget'
   Select-Combo 'Context budget' '{HOME}' '512 tokens'
   Assert-Combo 'Context budget' '512 tokens'
   Capture 'M03-OPT-06-retry-ready-candidate.png'
   Click-Control 'Retry turn'
   [void](Wait-Name 'Local model response completed and saved.' '' $false 640)
   $script:stage='independent retry receipt and original cancelled preservation'
   $retry=Read-PartialVault 'retry-saved'
   Wait-Assistant $retry.assistant_text
   Wait-Assistant $saved.assistant_text
   $retryControl=Wait-Name 'Retry turn' 'Button' $false
   if ($retryControl.Current.IsEnabled) {throw 'ZYN-RETRY-PROBE-002: completed turn remains retryable'}
   Capture 'M03-OPT-06-retry-completed-candidate.png'
   Stop-Native
   $script:stage='reopen completed retry in distinct process'
   Start-Native
   $retryReopenedPid=$script:app.Id
   if ($retryReopenedPid -in @($firstPid,$secondPid,$retryPid)) {throw 'ZYN-RETRY-PROBE-003: distinct process required'}
   Click-Control 'Chat'
   Click-Control 'P03 partial persistence'
   Wait-Assistant $saved.assistant_text
   Wait-Assistant $retry.assistant_text
   $retryControl=Wait-Name 'Retry turn' 'Button' $false
   if ($retryControl.Current.IsEnabled) {throw 'ZYN-RETRY-PROBE-004: reopened completed turn remains retryable'}
   Capture 'M03-OPT-06-retry-reopened-candidate.png'
   Stop-Native
   $null=Read-PartialVault 'retry-reopened'
   $retryImages=[ordered]@{}
   foreach ($name in @('M03-OPT-06-retry-ready-candidate.png','M03-OPT-06-retry-completed-candidate.png','M03-OPT-06-retry-reopened-candidate.png')) {
      $retryImages[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();retry_pid=$retryPid;reopened_pid=$retryReopenedPid;synthetic_only=$true;actual_model='qwen2.5:1.5b';context_limit=512;actual_native_retry=$true;retry_recovered_after_restart=$true;cancelled_response_preserved=$true;duplicate_user_message_absent=$true;completed_retry_disabled=$true;database_reopen_identity_verified=$true;images=$retryImages;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-retry-ui-proof.json') -Encoding utf8
   Write-Output 'P03 T05 actual Windows Retry after restart and independent database proof passed'
 } catch {
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;stage=$script:stage;status='FAILED_NOT_ACCEPTANCE';synthetic_only=$true;input_checks=@($script:inputChecks.ToArray())} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-partial-ui-failure.json') -Encoding utf8
   if ($script:hwnd -ne [IntPtr]::Zero -and $null -ne $script:root) {try {Capture 'DEBUG-native-partial-ui-failure.png'} catch {Write-Output 'Failure screenshot unavailable'}}
   throw
 } finally {Stop-Native}
 return
}

if ($ModelAcceptance) {
 try {
   $script:stage='model baseline identity'
   $null=Read-ModelVault 'baseline'
   $script:stage='real model first start'
   Start-Native
   $firstPid=$script:app.Id
   Click-Control 'Chat'
   [void](Wait-Name 'Conversation title' 'Edit' $true)
   $alpha='P03 model alpha'
   $beta='P03 model beta'
   $modelA='qwen2.5:0.5b'
   $modelB='qwen2.5:1.5b'
   $promptA='Reply with a short greeting.'
   $promptB='Say hello in three words.'
   $script:stage='create first model thread'
   Type-Exact 'Conversation title' $alpha
   Click-Control 'Create conversation'
   [void](Wait-Name 'Message' 'Edit' $true)
   Click-Control 'Refresh local models'
   [void](Wait-Name 'Model' 'ComboBox' $true)
   $script:stage='first installed model selection'
   Select-Combo 'Model' '{HOME}' $modelA
   $null=Read-ModelVault 'settings' $alpha $modelA 2048
   Assert-Combo 'Model' $modelA
   $script:stage='switch model in same thread'
   Select-Combo 'Model' '{END}' $modelB
   $null=Read-ModelVault 'settings' $alpha $modelB 2048
   Assert-Combo 'Model' $modelB
   Select-Combo 'Model' '{HOME}' $modelA
   $null=Read-ModelVault 'settings' $alpha $modelA 2048
   Select-Combo 'Context budget' '{HOME}' '512 tokens'
   $null=Read-ModelVault 'settings' $alpha $modelA 512
   Assert-Combo 'Context budget' '512 tokens'
   Capture 'M03-OPT-01-candidate.png'
   $script:stage='inspect first draft context'
   Type-Exact 'Message' $promptA
   Click-Control 'Inspect context'
   $estimateA=Wait-TextPattern '^Estimated [0-9]+ / 512 tokens'
   Capture 'M03-OPT-03-candidate.png'
   $script:stage='actual native send first model'
   Click-Control 'Send'
   [void](Wait-Name 'Local model response completed and saved.' '' $false 640)
   $savedA=Read-ModelVault 'turn' $alpha $modelA 512
   Wait-Assistant $savedA.assistant_text
   Capture 'M03-OPT-02-candidate.png'
   $script:stage='create second model thread'
   Type-Exact 'Conversation title' $beta
   Click-Control 'Create conversation'
   [void](Wait-Name 'Message' 'Edit' $true)
   Select-Combo 'Model' '{END}' $modelB
   $null=Read-ModelVault 'settings' $beta $modelB 2048
   Assert-Combo 'Model' $modelB
   Type-Exact 'Message' $promptB
   Click-Control 'Inspect context'
   $estimateB=Wait-TextPattern '^Estimated [0-9]+ / 2048 tokens'
   $script:stage='actual native send second model'
   Click-Control 'Send'
   [void](Wait-Name 'Local model response completed and saved.' '' $false 640)
   $savedB=Read-ModelVault 'turn' $beta $modelB 2048
   Wait-Assistant $savedB.assistant_text
   $script:stage='verify model database before restart'
   Stop-Native
   $null=Read-ModelVault 'saved'
   $script:stage='restart model UI'
   Start-Native
   $secondPid=$script:app.Id
   if ($firstPid -eq $secondPid) {throw 'ZYN-MODEL-PROBE-007: distinct process required'}
   Click-Control 'Chat'
   Click-Control $alpha
   Assert-Combo 'Model' $modelA
   Assert-Combo 'Context budget' '512 tokens'
   Wait-Assistant $savedA.assistant_text
   Click-Control $beta
   Assert-Combo 'Model' $modelB
   Assert-Combo 'Context budget' '2048 tokens'
   Wait-Assistant $savedB.assistant_text
   Capture 'M03-S04-candidate.png'
   Stop-Native
   $null=Read-ModelVault 'reopened'
   $images=[ordered]@{}
   foreach ($name in @('M03-OPT-01-candidate.png','M03-OPT-03-candidate.png','M03-OPT-02-candidate.png','M03-S04-candidate.png')) {
     $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   $proof=[ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();first_pid=$firstPid;reopened_pid=$secondPid;synthetic_only=$true;native_ui=$true;actual_model_send=$true;models=@($modelA,$modelB);same_thread_switch=$true;thread_settings_readback=$true;context_estimates=@($estimateA,$estimateB);ui_assistant_readback=$true;database_reopen_identity_verified=$true;keyboard_input_verified=$true;input_checks=@($script:inputChecks.ToArray());images=$images;visual_review='candidate_pending_visual_review';stop_retry_ui_verified=$false;full_accessibility_certified=$false}
   $proof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-model-ui-proof.json') -Encoding utf8
   Write-Output 'P03 actual Windows model selection, generation and restart verified'
 } catch {
   $failure=[ordered]@{schema_version=1;source_commit_sha=$SourceSha;stage=$script:stage;input_checks=@($script:inputChecks.ToArray());status='FAILED_NOT_ACCEPTANCE';synthetic_only=$true}
   $failure | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-model-ui-failure.json') -Encoding utf8
   if ($script:hwnd -ne [IntPtr]::Zero -and $null -ne $script:root) {
     try {Capture 'DEBUG-native-model-ui-failure.png'} catch {Write-Output 'Failure screenshot unavailable'}
   }
   throw
 } finally {Stop-Native}
 return
}

try {
 $script:stage='verify empty fixture'
 Read-Vault 'empty'
 $script:stage='first native start'
 Start-Native
 $firstPid=$script:app.Id
 Click-Control 'Chat'
 [void](Wait-Name 'Conversation title' 'Edit' $true)
 [void](Wait-Name 'No saved conversations.')
 Capture 'M03-S01-candidate.png'
 Type-Exact 'Conversation title' $title
 $script:stage='create conversation'
 Click-Control 'Create conversation'
 [void](Wait-Name 'Message' 'Edit' $true)
 Type-Exact 'Message' $content
 $script:stage='save message'
 Click-Control 'Save message'
 [void](Wait-Name $content)
 Stop-Native
 $script:stage='independent saved fixture check'
 Read-Vault 'saved'
 $script:stage='restart native app'
 Start-Native
 $secondPid=$script:app.Id
 if ($firstPid -eq $secondPid) {throw 'ZYN-CHAT-PROBE-016: process identity not distinct'}
 Click-Control 'Chat'
 $script:stage='reopen conversation from UI'
 Click-Control $title
 [void](Wait-Name $content)
 $composer=Wait-Name 'Message' 'Edit' $true
 Focus-Control $composer
 [void](Wait-Name $content)
 Capture 'M03-S02-candidate.png'
 Stop-Native
 $script:stage='independent reopened fixture check'
 Read-Vault 'reopened'
 $images=[ordered]@{}
 foreach ($name in @('M03-S01-candidate.png','M03-S02-candidate.png')) {
   $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
 }
 $proof=[ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();method='actual Windows Tauri UIA, real keyboard ValuePattern readback and independent read-only SQLite';first_pid=$firstPid;reopened_pid=$secondPid;synthetic_only=$true;empty_profile=$true;keyboard_input_verified=$true;input_checks=@($script:inputChecks.ToArray());ui_create_save=$true;ui_reopen_readback=$true;database_reopen_identity_verified=$true;images=$images;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false;model_inference_claimed=$false}
 $proof | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-chat-ui-proof.json') -Encoding utf8
 Write-Output 'P03 scoped real native chat interaction and independent restart readback passed'
} catch {
 $failure=[ordered]@{schema_version=1;source_commit_sha=$SourceSha;stage=$script:stage;input_checks=@($script:inputChecks.ToArray());status='FAILED_NOT_ACCEPTANCE';synthetic_only=$true}
 $failure | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-chat-ui-failure.json') -Encoding utf8
 if ($script:hwnd -ne [IntPtr]::Zero -and $null -ne $script:root) {
   try {Capture 'DEBUG-native-ui-failure.png'} catch {Write-Output 'Failure screenshot unavailable'}
 }
 throw
} finally {Stop-Native}
