# Actual Windows WebView2 keyboard/UI Automation probe, synthetic runner profile only.
param(
 [Parameter(Mandatory=$true)][string]$Executable,
 [Parameter(Mandatory=$true)][string]$SourceSha,
 [Parameter(Mandatory=$true)][string]$OutputDirectory,
 [switch]$ModelAcceptance,
 [switch]$AttachmentAcceptance,
 [switch]$PartialAcceptance,
 [switch]$ArtifactAcceptance,
 [switch]$ReviewAcceptance,
 [switch]$ExportAcceptance,
 [switch]$BackupAcceptance,
 [string]$PriorModelProofDirectory='',
 [string]$OllamaExecutable=''
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
   try {
     $pattern.Invoke()
     Write-Output ('Native activation: '+$Name+' via InvokePattern')
   } catch {
     # Never repeat a mutation after an ambiguous provider acknowledgement.
     # Only the bounded, read-only recovery inventory may be activated again.
     if ($Name -cne 'Check managed files') {throw}
     Write-Output ('Native recovery activation: InvokePattern failed; class='+$_.Exception.GetType().Name)
     $reportCondition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'Managed file check result')
     $existingReport=$null
     for ($attempt=0;$attempt -lt 8;$attempt++) {
       $existingReport=$script:root.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$reportCondition)
       if ($null -ne $existingReport) {break}
       Start-Sleep -Milliseconds 250
     }
     if ($null -ne $existingReport) {
       Write-Output 'Native recovery activation: report already present; no repeat click'
     } else {
       $freshControl=Wait-Name 'Check managed files' 'Button' $true
       Focus-ByPhysicalClick $freshControl
       Write-Output 'Native recovery activation: bounded physical click on freshly acquired read-only control'
     }
     # Caller must still read all eight exact visible counts and verify the
     # database, managed blob and interrupted stage independently.
   }
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
function Wait-RecoveryCounts {
 $expected=@('Referenced hashes: 1','Verified referenced: 1','Unavailable referenced: 0','Verified unreferenced: 0','Damaged or unreadable: 0','Interrupted stages: 1','Unexpected entries: 0','Unlinked metadata: 0')
 $groupCondition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'Managed file check result')
 $seen=[System.Collections.Generic.List[string]]::new()
 foreach ($name in $expected) {
   $matched=$false
   $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$name)
   for ($attempt=0;$attempt -lt 80 -and !$matched;$attempt++) {
     foreach ($group in $script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$groupCondition)) {
       foreach ($item in $group.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)) {
         try {
           $rect=$item.Current.BoundingRectangle
           if (!$item.Current.IsOffscreen -and !$rect.IsEmpty -and $rect.Width -gt 0 -and $rect.Height -gt 0) {
             $matched=$true;break
           }
           $scroll=$null
           if ($item.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$scroll)) {$scroll.ScrollIntoView()}
           elseif ($item.Current.IsKeyboardFocusable) {$item.SetFocus()}
         } catch [System.Windows.Automation.ElementNotAvailableException] {}
       }
       if ($matched) {break}
     }
     if (!$matched) {Start-Sleep -Milliseconds 250}
   }
   if (!$matched) {
     $names=[System.Collections.Generic.List[object]]::new()
     foreach ($group in $script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$groupCondition)) {
       foreach ($item in $group.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)) {
         try {if ($names.Count -lt 100) {$names.Add([ordered]@{name=$item.Current.Name;type=$item.Current.ControlType.ProgrammaticName;offscreen=$item.Current.IsOffscreen})}}
         catch [System.Windows.Automation.ElementNotAvailableException] {}
       }
     }
     ConvertTo-Json -InputObject @($names.ToArray()) -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'synthetic-recovery-uia.json') -Encoding utf8
     throw ('ZYN-RECOVERY-PROBE-004: exact visible recovery count missing: '+$name)
   }
   $seen.Add($name)
 }
 return @($seen.ToArray())
}
function Read-ArtifactVault([string]$Stage) {
 $result=& python scripts/verify_p03_text_artifact_ui_database.py --stage $Stage --output $OutputDirectory --attachment-proof (Join-Path $env:RUNNER_TEMP 'p03-attachment-ui-proof')
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-ARTIFACT-PROBE-001: independent artifact database verification failed'}
 return ($result | ConvertFrom-Json)
}
function Wait-ArtifactPreview([string]$Expected) {
 # UIA ValuePattern reads the real readonly textarea; no DOM injection.
 # Windows may normalize line endings in the text control. The verifier
 # independently checks exact UTF-8 bytes, including original line endings.
 $normalized=$Expected -replace '\r\n',"`n"
 $groupCondition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'Verified text artifact preview')
 $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'Verified artifact text')
 for ($attempt=0;$attempt -lt 80;$attempt++) {
   foreach ($group in $script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$groupCondition)) {
     foreach ($item in $group.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)) {
       try {
         if ($item.Current.ControlType.ProgrammaticName -ne 'ControlType.Edit') {continue}
         $value=$null
         if (!$item.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$value) -or !$value.Current.IsReadOnly) {continue}
         if (($value.Current.Value -replace '\r\n',"`n") -cne $normalized) {continue}
         $rect=$item.Current.BoundingRectangle
         if (!$item.Current.IsOffscreen -and !$rect.IsEmpty -and $rect.Width -gt 0 -and $rect.Height -gt 0) {return}
         Focus-Control $item
       } catch [System.Windows.Automation.ElementNotAvailableException] {}
     }
   }
   Start-Sleep -Milliseconds 250
 }
 throw 'ZYN-ARTIFACT-PROBE-002: verified readonly artifact text not visible or exact'
}
function Read-ReviewVault([string]$Stage) {
 $result=& python scripts/verify_p03_review_ui_database.py --stage $Stage --output $OutputDirectory --artifact-proof (Join-Path $env:RUNNER_TEMP 'p03-text-artifact-ui-proof')
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-REVIEW-PROBE-001: independent review DB proof failed'}
 return ($result | ConvertFrom-Json)
}
function Wait-ReviewDecision([string]$Name) {
 $row=Wait-Name $Name 'ListItem'
 Focus-Control $row
 if ($row.Current.IsOffscreen -or $row.Current.BoundingRectangle.IsEmpty) {throw 'ZYN-REVIEW-PROBE-002: decision not visible'}
}
function Read-BackupVault([string]$Stage) {
 $result=& python scripts/verify_p03_backup_ui_database.py --stage $Stage --output $OutputDirectory --export-proof (Join-Path $env:RUNNER_TEMP 'p03-export-ui-proof')
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-BACKUP-PROBE-001: independent backup verification failed'}
 return ($result | ConvertFrom-Json)
}
function Type-SyntheticSecret([string]$Name,[string]$Secret) {
 # Disposable fixture password only, never read password values or log them.
 if ($Secret -cnotmatch '^[A-Za-z0-9 ]{12,64}$') {throw 'ZYN-BACKUP-PROBE-002: invalid fixture secret'}
 $control=Wait-Name $Name 'Edit' $true
 if (!$control.Current.IsPassword) {throw 'ZYN-BACKUP-PROBE-003: input is not masked'}
 Focus-Control $control
 $focused=[System.Windows.Automation.AutomationElement]::FocusedElement
 if ($focused.Current.Name -cne $Name -or !$focused.Current.IsPassword) {throw 'ZYN-BACKUP-PROBE-004: password focus mismatch'}
 [System.Windows.Forms.SendKeys]::SendWait('^a')
 [System.Windows.Forms.SendKeys]::SendWait('{BACKSPACE}')
 foreach ($char in $Secret.ToCharArray()) {[System.Windows.Forms.SendKeys]::SendWait([string]$char);Start-Sleep -Milliseconds 30}
}
function Consent-Backup([string]$Name) {
 $control=Wait-Name $Name 'CheckBox' $true
 Focus-Control $control
 $toggle=$null
 if (!$control.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$toggle) -or $toggle.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::Off) {throw 'ZYN-BACKUP-PROBE-005: consent unavailable or preselected'}
 $toggle.Toggle()
}
if ($BackupAcceptance) {
 try {
   if ($AttachmentAcceptance -or $PartialAcceptance -or $ModelAcceptance -or $ArtifactAcceptance -or $ReviewAcceptance -or $ExportAcceptance) {throw 'ZYN-BACKUP-PROBE-006: mutually exclusive journeys'}
   $script:stage='backup baseline after export proof'
   $null=Read-BackupVault 'baseline'
   Start-Native
   $firstPid=$script:app.Id
   Click-Control 'Backup Center'
   $script:stage='native encrypted archive creation'
   Type-SyntheticSecret 'Backup passphrase' 'synthetic backup fixture 2026'
   Type-SyntheticSecret 'Confirm backup passphrase' 'synthetic backup fixture 2026'
   Consent-Backup 'I choose the local portable backup folder and understand recovery requires the passphrase'
   Click-Control 'Create encrypted backup'
   $idControl=Wait-Name 'Verified backup ID' 'Edit' $false 480
   $value=$idControl.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
   if (!$value.Current.IsReadOnly) {throw 'ZYN-BACKUP-PROBE-007: backup receipt editable'}
   $backupId=$value.Current.Value
   if ($backupId -cnotmatch '^[A-Za-z0-9-]{16,64}$') {throw 'ZYN-BACKUP-PROBE-008: invalid backup receipt'}
   Focus-Control $idControl
   Capture 'M23-OPT-07-encrypted-backup-candidate.png'
   Stop-Native
   $saved=Read-BackupVault 'saved'
   if ($saved.backup_id -cne $backupId) {throw 'ZYN-BACKUP-PROBE-009: archive receipt mismatch'}
   $script:stage='restart and wrong passphrase rejection'
   Start-Native
   $secondPid=$script:app.Id
   if ($secondPid -eq $firstPid) {throw 'ZYN-BACKUP-PROBE-010: distinct process required'}
   Click-Control 'Backup Center'
   Type-Exact 'Backup ID to restore' $backupId
   Type-SyntheticSecret 'Backup passphrase' 'incorrect fixture passphrase'
   Consent-Backup 'I understand restore creates a separate plaintext profile without replacing active data'
   Click-Control 'Verify and restore to new profile'
   [void](Wait-Name 'Backup authentication failed. Check the passphrase or use an intact archive. No active profile was replaced. Check the recorded operation ID and local folder before another attempt.' '' $false 480)
   Stop-Native
   $null=Read-BackupVault 'wrong'
   $script:stage='authenticated restore into separate profile'
   Start-Native
   $thirdPid=$script:app.Id
   if ($thirdPid -in @($firstPid,$secondPid)) {throw 'ZYN-BACKUP-PROBE-011: distinct process required'}
   Click-Control 'Backup Center'
   Type-Exact 'Backup ID to restore' $backupId
   Type-SyntheticSecret 'Backup passphrase' 'synthetic backup fixture 2026'
   Consent-Backup 'I understand restore creates a separate plaintext profile without replacing active data'
   Click-Control 'Verify and restore to new profile'
   $restore=Wait-Name 'Relative restored profile path' 'Edit' $false 480
   $value=$restore.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
   if (!$value.Current.IsReadOnly) {throw 'ZYN-BACKUP-PROBE-012: restore receipt editable'}
   $relative=$value.Current.Value
   Focus-Control $restore
   Capture 'M23-OPT-09-restore-preview-candidate.png'
   Stop-Native
   $proof=Read-BackupVault 'restored'
   if ($proof.relative_path -cne $relative) {throw 'ZYN-BACKUP-PROBE-013: restored profile receipt mismatch'}
   $images=[ordered]@{}
   foreach ($name in @('M23-OPT-07-encrypted-backup-candidate.png','M23-OPT-09-restore-preview-candidate.png')) {
      $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();first_pid=$firstPid;wrong_key_pid=$secondPid;restored_pid=$thirdPid;synthetic_only=$true;actual_native_backup=$true;wrong_key_rejected=$true;actual_native_separate_restore=$true;independent_db_and_blob_comparison=$true;active_profile_preserved=$true;images=$images;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-backup-ui-proof.json') -Encoding utf8
 } catch {
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;stage=$script:stage;status='FAILED_NOT_ACCEPTANCE';synthetic_only=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-backup-ui-failure.json') -Encoding utf8
   # Never capture an error screenshot while password fields could contain input.
   throw
 } finally {Stop-Native}
 return
}
function Read-ExportVault([string]$Stage) {
 $result=& python scripts/verify_p03_export_ui_database.py --stage $Stage --output $OutputDirectory --review-proof (Join-Path $env:RUNNER_TEMP 'p03-review-ui-proof')
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-EXPORT-PROBE-001: independent export verification failed'}
 return ($result | ConvertFrom-Json)
}
if ($ExportAcceptance) {
 try {
   if ($AttachmentAcceptance -or $PartialAcceptance -or $ModelAcceptance -or $ArtifactAcceptance -or $ReviewAcceptance) {throw 'ZYN-EXPORT-PROBE-002: mutually exclusive journeys'}
   $script:stage='export baseline after review proof'
   $null=Read-ExportVault 'baseline'
   Start-Native
   $firstPid=$script:app.Id
   Click-Control 'Chat'
   Click-Control 'P03 attachment proof'
   $script:stage='explicit native plaintext export consent'
   $checkbox=Wait-Name 'I understand the export is unencrypted and choose the local exports folder' 'CheckBox' $true
   Focus-Control $checkbox
   $toggle=$null
   if (!$checkbox.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$toggle)) {throw 'ZYN-EXPORT-PROBE-003: consent toggle unavailable'}
   if ($toggle.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::Off) {throw 'ZYN-EXPORT-PROBE-004: consent preselected'}
   Capture 'M03-S06-export-consent-candidate.png'
   $toggle.Toggle()
   Click-Control 'Export full conversation'
   $path=Wait-Name 'Relative export path' 'Edit'
   $value=$null
   if (!$path.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$value) -or !$value.Current.IsReadOnly) {throw 'ZYN-EXPORT-PROBE-005: receipt not readonly'}
   $relative=$value.Current.Value
   if ($relative -cnotmatch '^data/exports/conversation-[A-Za-z0-9-]{16,64}\.json$') {throw 'ZYN-EXPORT-PROBE-006: invalid receipt path'}
   Focus-Control $path
   Capture 'M03-OPT-07-export-candidate.png'
   Stop-Native
   $script:stage='independent exact export contents'
   $saved=Read-ExportVault 'saved'
   if ($saved.relative_path -cne $relative) {throw 'ZYN-EXPORT-PROBE-007: UI path mismatch'}
   Start-Native
   $secondPid=$script:app.Id
   if ($firstPid -eq $secondPid) {throw 'ZYN-EXPORT-PROBE-008: distinct process required'}
   Stop-Native
   $null=Read-ExportVault 'reopened'
   $images=[ordered]@{}
   foreach ($name in @('M03-S06-export-consent-candidate.png','M03-OPT-07-export-candidate.png')) {
      $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();first_pid=$firstPid;reopened_pid=$secondPid;synthetic_only=$true;actual_native_consent=$true;actual_native_export=$true;readonly_receipt_path=$true;independent_contents_and_restart_verified=$true;images=$images;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-export-ui-proof.json') -Encoding utf8
 } catch {
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;stage=$script:stage;status='FAILED_NOT_ACCEPTANCE';synthetic_only=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-export-ui-failure.json') -Encoding utf8
   if ($script:hwnd -ne [IntPtr]::Zero -and $null -ne $script:root) {try {Capture 'DEBUG-native-export-ui-failure.png'} catch {Write-Output 'Failure screenshot unavailable'}}
   throw
 } finally {Stop-Native}
 return
}
if ($ReviewAcceptance) {
 try {
   if ($AttachmentAcceptance -or $PartialAcceptance -or $ModelAcceptance -or $ArtifactAcceptance) {throw 'ZYN-REVIEW-PROBE-003: mutually exclusive journeys'}
   $script:stage='review baseline after T09 proof'
   $null=Read-ReviewVault 'baseline'
   $script:stage='native pending and explicit deny'
   Start-Native
   $firstPid=$script:app.Id
   Click-Control 'Chat'
   Click-Control 'P03 model beta'
   Click-Control 'Review text artifact tool from message 2'
   $button=Wait-Name 'Deny local tool' 'Button' $true
   Focus-Control $button
   Capture 'M03-S05-review-pending-candidate.png'
   Click-Control 'Deny local tool'
   Wait-ReviewDecision 'Tool decision: deny local.write_artifact'
   Capture 'M03-OPT-08-denied-candidate.png'
   Stop-Native
   $null=Read-ReviewVault 'denied'
   $script:stage='native reopened denial and explicit approval'
   Start-Native
   $secondPid=$script:app.Id
   if ($secondPid -eq $firstPid) {throw 'ZYN-REVIEW-PROBE-004: distinct process required'}
   Click-Control 'Chat'
   Click-Control 'P03 model beta'
   Click-Control 'Refresh tool trace'
   Wait-ReviewDecision 'Tool decision: deny local.write_artifact'
   Click-Control 'Review text artifact tool from message 2'
   Click-Control 'Approve local tool'
   Wait-ReviewDecision 'Tool decision: approve local.write_artifact'
   Capture 'M03-OPT-08-approved-candidate.png'
   Click-Control 'Preview text artifact from receipt 3'
   Click-Control 'Close artifact preview'
   Click-Control 'P03 attachment proof'
   Click-Control 'Review attachment tool p03-attachment-fixture.bin'
   Click-Control 'Approve local tool'
   Wait-ReviewDecision 'Tool decision: approve local.read_attachment'
   Capture 'M03-OPT-08-attachment-approved-candidate.png'
   Stop-Native
   $null=Read-ReviewVault 'approved'
   $script:stage='restart and actual review trace readback'
   Start-Native
   $thirdPid=$script:app.Id
   if ($thirdPid -in @($firstPid,$secondPid)) {throw 'ZYN-REVIEW-PROBE-005: distinct process required'}
   Click-Control 'Chat'
   Click-Control 'P03 model beta'
   Click-Control 'Refresh tool trace'
   Wait-ReviewDecision 'Tool decision: deny local.write_artifact'
   Wait-ReviewDecision 'Tool decision: approve local.write_artifact'
   Capture 'M03-OPT-08-reopened-candidate.png'
   Click-Control 'P03 attachment proof'
   Click-Control 'Refresh tool trace'
   Wait-ReviewDecision 'Tool decision: approve local.read_attachment'
   Capture 'M03-OPT-08-attachment-reopened-candidate.png'
   Stop-Native
   $null=Read-ReviewVault 'reopened'
   $images=[ordered]@{}
   foreach ($name in @('M03-S05-review-pending-candidate.png','M03-OPT-08-denied-candidate.png','M03-OPT-08-approved-candidate.png','M03-OPT-08-reopened-candidate.png','M03-OPT-08-attachment-approved-candidate.png','M03-OPT-08-attachment-reopened-candidate.png')) {
     $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();first_pid=$firstPid;approved_pid=$secondPid;reopened_pid=$thirdPid;synthetic_only=$true;actual_native_denial=$true;actual_native_approval=$true;actual_attachment_verification_approval=$true;reopened_trace=$true;independent_db_and_blob_proof=$true;images=$images;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-review-ui-proof.json') -Encoding utf8
 } catch {
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;stage=$script:stage;status='FAILED_NOT_ACCEPTANCE';synthetic_only=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-review-ui-failure.json') -Encoding utf8
   if ($script:hwnd -ne [IntPtr]::Zero -and $null -ne $script:root) {try {Capture 'DEBUG-native-review-ui-failure.png'} catch {Write-Output 'Failure screenshot unavailable'}}
   throw
 } finally {Stop-Native}
 return
}
if ($ArtifactAcceptance) {
 try {
   if ($AttachmentAcceptance -or $PartialAcceptance -or $ModelAcceptance) {throw 'ZYN-ARTIFACT-PROBE-003: mutually exclusive journeys'}
   $script:stage='artifact baseline after attachment and recovery proof'
   $baseline=Read-ArtifactVault 'baseline'
   $script:stage='actual native artifact creation from saved model response'
   Start-Native
   $firstPid=$script:app.Id
   Click-Control 'Chat'
   Click-Control 'P03 model alpha'
   Click-Control 'Generate text artifact from message 2'
   Wait-ArtifactPreview $baseline.assistant_text
   Capture 'M03-OPT-05-candidate.png'
   Stop-Native
   $script:stage='independent committed artifact receipt'
   $null=Read-ArtifactVault 'saved'
   $script:stage='restart and explicit artifact preview'
   Start-Native
   $secondPid=$script:app.Id
   if ($firstPid -eq $secondPid) {throw 'ZYN-ARTIFACT-PROBE-004: distinct process required'}
   Click-Control 'Chat'
   Click-Control 'P03 model alpha'
   Click-Control 'Preview text artifact from receipt 3'
   Wait-ArtifactPreview $baseline.assistant_text
   Capture 'M03-OPT-05-reopened-candidate.png'
   Click-Control 'Close artifact preview'
   Stop-Native
   $null=Read-ArtifactVault 'reopened'
   $script:stage='restart and repeat same source creation'
   Start-Native
   $thirdPid=$script:app.Id
   if ($thirdPid -in @($firstPid,$secondPid)) {throw 'ZYN-ARTIFACT-PROBE-005: distinct replay process required'}
   Click-Control 'Chat'
   Click-Control 'P03 model alpha'
   Click-Control 'Generate text artifact from message 2'
   Wait-ArtifactPreview $baseline.assistant_text
   Capture 'M03-OPT-05-replayed-candidate.png'
   Stop-Native
   $null=Read-ArtifactVault 'replayed'
   $images=[ordered]@{}
   foreach ($name in @('M03-OPT-05-candidate.png','M03-OPT-05-reopened-candidate.png','M03-OPT-05-replayed-candidate.png')) {
      $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();first_pid=$firstPid;reopened_pid=$secondPid;replayed_pid=$thirdPid;synthetic_only=$true;source_is_real_saved_model_response=$true;actual_native_creation=$true;readonly_preview_exact_readback=$true;actual_native_reopen_preview=$true;actual_native_replay=$true;no_duplicate_receipt=$true;prior_attachment_and_stage_preserved=$true;database_blob_reopen_verified=$true;images=$images;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-text-artifact-ui-proof.json') -Encoding utf8
 } catch {
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;stage=$script:stage;status='FAILED_NOT_ACCEPTANCE';synthetic_only=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-text-artifact-ui-failure.json') -Encoding utf8
   if ($script:hwnd -ne [IntPtr]::Zero -and $null -ne $script:root) {try {Capture 'DEBUG-native-text-artifact-ui-failure.png'} catch {Write-Output 'Failure screenshot unavailable'}}
   throw
 } finally {Stop-Native}
 return
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
   $script:stage='prepare disposable interrupted managed stage fixture'
   $attachmentReceipt=Get-Content -LiteralPath (Join-Path $OutputDirectory 'p03-attachment-db-reopened.json') -Raw | ConvertFrom-Json
   if ($attachmentReceipt.sha256 -cnotmatch '^[a-f0-9]{64}$' -or $attachmentReceipt.bytes -ne 70000) {throw 'ZYN-RECOVERY-PROBE-001: invalid fixture receipt'}
   $managedRoot=Join-Path $env:LOCALAPPDATA 'com.zynoa.desktop\data\artifacts\sha256'
   $managedDirectory=Join-Path $managedRoot $attachmentReceipt.sha256.Substring(0,2)
   $stagePath=Join-Path $managedDirectory '.stage-1-2-3'
   if (!(Test-Path -LiteralPath (Join-Path $managedDirectory $attachmentReceipt.sha256) -PathType Leaf) -or (Test-Path -LiteralPath $stagePath)) {throw 'ZYN-RECOVERY-PROBE-002: unexpected managed fixture inventory'}
   $stageStream=[IO.File]::Open($stagePath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
   try {$stageBytes=[Text.Encoding]::UTF8.GetBytes('synthetic interrupted stage');$stageStream.Write($stageBytes,0,$stageBytes.Length);$stageStream.Flush($true)} finally {$stageStream.Dispose()}
   $script:stage='actual native recovery inspection after restart'
   Start-Native
   $recoveryPid=$script:app.Id
   if ($recoveryPid -in @($firstPid,$secondPid)) {throw 'ZYN-RECOVERY-PROBE-003: distinct process required'}
   Click-Control 'Chat'
   Click-Control 'P03 attachment proof'
   Click-Control 'Check managed files'
   $recoveryCounts=@(Wait-RecoveryCounts)
   if ($recoveryCounts.Count -ne 8) {throw 'ZYN-RECOVERY-PROBE-005: incomplete native recovery count readback'}
   Capture 'M03-managed-recovery-candidate.png'
   Stop-Native
   $script:stage='independent recovery stage and prior DB preservation'
   Read-AttachmentVault 'recovery'
   $images=[ordered]@{}
   foreach ($name in @('M03-S03-candidate.png','M03-OPT-04-candidate.png','M03-managed-recovery-candidate.png')) {
     $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();first_pid=$firstPid;reopened_pid=$secondPid;synthetic_only=$true;actual_os_picker=$true;remove_reselect=$true;original_removed=$true;database_blob_reopen_verified=$true;ui_filename_readback=$true;actual_recovery_inspection=$true;recovery_counts=$recoveryCounts;recovery_pid=$recoveryPid;interrupted_stage_preserved=$true;input_checks=@($script:inputChecks.ToArray());images=$images;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false;model_ingestion_claimed=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-attachment-ui-proof.json') -Encoding utf8
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
function Read-FixtureInventory {
 $inventory=Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -NoProxy -TimeoutSec 10
 return @($inventory.models)
}
function Invoke-FixtureModelCommand([string[]]$Arguments) {
 # This mutates only the pinned disposable runner model store, never user models.
 $expectedStore=Join-Path $env:RUNNER_TEMP 'p03-windows-models'
 $runtimeRoot=Join-Path $env:RUNNER_TEMP 'p03-ollama-windows'
 if ($env:GITHUB_ACTIONS -cne 'true' -or !$OllamaExecutable -or !$env:OLLAMA_MODELS -or
     [IO.Path]::GetFullPath($env:OLLAMA_MODELS) -ine [IO.Path]::GetFullPath($expectedStore) -or
     $env:OLLAMA_HOST -cne '127.0.0.1:11434' -or $env:OLLAMA_NO_CLOUD -cne '1' -or
     !(Test-Path -LiteralPath $OllamaExecutable -PathType Leaf) -or
     ![IO.Path]::GetFullPath($OllamaExecutable).StartsWith([IO.Path]::GetFullPath($runtimeRoot)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
   throw 'ZYN-MODEL-AVAIL-001: disposable runtime identity required'
 }
 & $OllamaExecutable @Arguments
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-MODEL-AVAIL-002: fixture model command failed'}
}
function Assert-NoContextEstimate {
 $items=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 foreach ($item in $items) {
   try {if ([string]$item.Current.Name -match '^Estimated [0-9]+ / [0-9]+ tokens') {throw 'ZYN-MODEL-AVAIL-003: stale context estimate survived refresh'}}
   catch [System.Windows.Automation.ElementNotAvailableException] {}
 }
}
function Assert-ModelControlBounds([bool]$Missing) {
 # Actual HWND-owned UIA rectangles, not DOM measurements or a mockup.
 # Only horizontal containment is asserted; vertical scrolling and complete
 # accessibility certification remain independent acceptance requirements.
 $group=Wait-Name 'Local model and context settings' '' $false
 $bounds=$group.Current.BoundingRectangle
 $window=New-Object ChatProbeWindow+RECT
 if (![ChatProbeWindow]::GetWindowRect($script:hwnd,[ref]$window) -or $bounds.IsEmpty -or $bounds.Width -le 0 -or
     $bounds.Left -lt ($window.Left-2) -or $bounds.Right -gt ($window.Right+2)) {
   throw 'ZYN-MODEL-LAYOUT-001: settings group outside native window'
 }
 $controls=@(
   @{Name='Model';Type='ComboBox'},
   @{Name='Context budget';Type='ComboBox'},
   @{Name='Inspect context';Type='Button'}
 )
 if ($Missing) {
   $controls+=@{Name='The saved model is unavailable. Refresh local models or choose an installed model. Your saved messages are unchanged.';Type=''}
 }
 $measured=@()
 foreach ($spec in $controls) {
   $control=Wait-Name $spec.Name $spec.Type $false
   $rect=$control.Current.BoundingRectangle
   if ($rect.IsEmpty -or $rect.Width -le 0 -or $rect.Left -lt ($bounds.Left-2) -or $rect.Right -gt ($bounds.Right+2)) {
     throw ('ZYN-MODEL-LAYOUT-002: control outside settings group: '+$spec.Name)
   }
   $measured+=@{name=$spec.Name;left=$rect.Left;right=$rect.Right;width=$rect.Width}
 }
 return @{missing=$Missing;group_left=$bounds.Left;group_right=$bounds.Right;controls=$measured}
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
   $script:stage='model availability baseline'
   $null=Read-PartialVault 'retry-check'
   $originalModel='qwen2.5:0.5b'
   $otherModel='qwen2.5:1.5b'
   $alias='p03-availability-restore:latest'
   $before=@(Read-FixtureInventory)
   $original=@($before | Where-Object {$_.name -ceq $originalModel})
   if ($before.Count -ne 2 -or $original.Count -ne 1 -or @($before | Where-Object {$_.name -ceq $otherModel}).Count -ne 1 -or @($before | Where-Object {$_.name -ceq $alias}).Count -ne 0) {throw 'ZYN-MODEL-AVAIL-004: unexpected baseline inventory'}
   Start-Native
   $availabilityPid=$script:app.Id
   Click-Control 'Chat'
   Click-Control 'P03 model alpha'
   Assert-Combo 'Model' $originalModel
   Assert-Combo 'Context budget' '512 tokens'
   Type-Exact 'Message' 'Hello again.'
   Click-Control 'Inspect context'
   $estimateBefore=Wait-TextPattern '^Estimated [0-9]+ / 512 tokens'
   [void](Wait-Name 'Send' 'Button' $true)
   $script:stage='copy fixture model for reversible removal'
   Invoke-FixtureModelCommand @('cp',$originalModel,$alias)
   $copied=@(Read-FixtureInventory)
   $backup=@($copied | Where-Object {$_.name -ceq $alias})
   if ($copied.Count -ne 3 -or $backup.Count -ne 1 -or $backup[0].digest -cne $original[0].digest) {throw 'ZYN-MODEL-AVAIL-005: restore alias identity mismatch'}
   try {
     $script:stage='actual saved model missing after refresh'
     Invoke-FixtureModelCommand @('rm',$originalModel)
     $missing=@(Read-FixtureInventory)
     if ($missing.Count -ne 2 -or @($missing | Where-Object {$_.name -ceq $originalModel}).Count -ne 0 -or @($missing | Where-Object {$_.name -ceq $otherModel}).Count -ne 1) {throw 'ZYN-MODEL-AVAIL-006: original model still installed'}
     Click-Control 'Refresh local models'
     Assert-Combo 'Model' 'Previously selected model unavailable'
     [void](Wait-Name 'The saved model is unavailable. Refresh local models or choose an installed model. Your saved messages are unchanged.')
     $send=Wait-Name 'Send' 'Button' $false
     if ($send.Current.IsEnabled) {throw 'ZYN-MODEL-AVAIL-007: Send enabled for missing saved model with nonempty draft'}
     Assert-NoContextEstimate
     $null=Read-PartialVault 'retry-check'
     $missingBounds=Assert-ModelControlBounds $true
     Capture 'M03-OPT-01-missing-model-candidate.png'
   } finally {
     # Restore the exact original digest before removing its temporary alias.
     $current=@(Read-FixtureInventory)
     if (@($current | Where-Object {$_.name -ceq $originalModel}).Count -eq 0) {
       Invoke-FixtureModelCommand @('cp',$alias,$originalModel)
     }
     $restored=@(Read-FixtureInventory | Where-Object {$_.name -ceq $originalModel})
     if ($restored.Count -ne 1 -or $restored[0].digest -cne $original[0].digest) {throw 'ZYN-MODEL-AVAIL-008: original digest not restored; preserve alias'}
     Invoke-FixtureModelCommand @('rm',$alias)
   }
   $script:stage='actual model restoration and context refresh'
   $after=@(Read-FixtureInventory)
   $beforeIdentity=@($before | Sort-Object name | Select-Object name,digest | ConvertTo-Json -Compress)
   $afterIdentity=@($after | Sort-Object name | Select-Object name,digest | ConvertTo-Json -Compress)
   if (($beforeIdentity -join '') -cne ($afterIdentity -join '')) {throw 'ZYN-MODEL-AVAIL-009: restored inventory changed'}
   Click-Control 'Refresh local models'
   Assert-Combo 'Model' $originalModel
   Assert-Combo 'Context budget' '512 tokens'
   [void](Wait-Name 'Send' 'Button' $true)
   Assert-NoContextEstimate
   Click-Control 'Inspect context'
   $estimateAfter=Wait-TextPattern '^Estimated [0-9]+ / 512 tokens'
   if ($estimateBefore -cne $estimateAfter) {throw 'ZYN-MODEL-AVAIL-010: identical draft/history context changed'}
   $restoredBounds=Assert-ModelControlBounds $false
   Capture 'M03-OPT-01-restored-model-candidate.png'
   Click-Control 'Clear draft'
   Stop-Native
   $identity=Read-PartialVault 'retry-check'
   $availabilityImages=[ordered]@{}
   foreach ($name in @('M03-OPT-01-missing-model-candidate.png','M03-OPT-01-restored-model-candidate.png')) {
     $availabilityImages[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
   }
   [ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();pid=$availabilityPid;synthetic_only=$true;actual_model=$originalModel;model_digest=$original[0].digest;other_model_present=$true;actual_model_removal=$true;missing_placeholder_verified=$true;send_disabled_with_draft=$true;inventory_restored=$true;original_preference_preserved=$true;stale_context_invalidated=$true;context_estimates=@($estimateBefore,$estimateAfter);prior_database_fingerprint=$identity.fingerprint;horizontal_layout_bounds=@($missingBounds,$restoredBounds);images=$availabilityImages;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-model-availability-ui-proof.json') -Encoding utf8
   Write-Output 'P03 T06 actual missing-model and restoration UI proof passed'
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
