# Actual Windows WebView2 keyboard/UI Automation probe, synthetic runner profile only.
param(
 [Parameter(Mandatory=$true)][string]$Executable,
 [Parameter(Mandatory=$true)][string]$SourceSha,
 [Parameter(Mandatory=$true)][string]$OutputDirectory,
 [switch]$ModelAcceptance
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
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);

 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
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
       if (!$e.Current.IsOffscreen -or $Type) {return $e}
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
   if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-MODEL-PROBE-002: foreground lost'}
   $actualKey=$Key
   if ($attempt -eq 2 -and $Name -ceq 'Model' -and $Key -ceq '{HOME}') {$actualKey='q'}
   [System.Windows.Forms.SendKeys]::SendWait($actualKey)
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
       if (([string]$item.Current.Name -replace '\s+',' ').Trim() -ceq $normalized -and !$item.Current.IsOffscreen) {return}
     } catch [System.Windows.Automation.ElementNotAvailableException] {}
   }
   Start-Sleep -Milliseconds 250
 }
 throw 'ZYN-MODEL-PROBE-006: persisted assistant text not visible in native UI'
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
