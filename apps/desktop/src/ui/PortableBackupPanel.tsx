import {useRef,useState} from "react";
import {chatRequest,chatError,mutationId} from "../chat-transport";
import {byteLength,type BackupReceipt,type RestoreReceipt} from "./chat-contract";
export function PortableBackupPanel({connected}:{connected:boolean}){
 const [password,setPassword]=useState(""),[confirm,setConfirm]=useState(""),[backupId,setBackupId]=useState("");
 const [createConsent,setCreateConsent]=useState(false),[restoreConsent,setRestoreConsent]=useState(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState(""),[operation,setOperation]=useState("");
 const [backup,setBackup]=useState<BackupReceipt|null>(null),[restored,setRestored]=useState<RestoreReceipt|null>(null);
 const lock=useRef(false);
 const valid=byteLength(password)>=12&&byteLength(password)<=1024&&!password.includes("\0");
 const ready=connected&&!busy;
 async function perform(kind:"create"|"restore"){
   if(!ready||!valid||lock.current)return;
   if(kind==="create"&&(!createConsent||password!==confirm))return;
   if(kind==="restore"&&(!restoreConsent||!/^[A-Za-z0-9-]{16,64}$/.test(backupId)))return;
   lock.current=true;setBusy(true);setError("");setOperation("");
   const secret=password;setPassword("");setConfirm("");setCreateConsent(false);setRestoreConsent(false);
   try{
     const id=mutationId();setOperation(id);
     if(kind==="create"){
       setBackup(null);const receipt=await chatRequest("chat.backup.create",{backupId:id,passphrase:secret});
       setBackup(receipt);setBackupId(receipt.backupId);
     }else{
       setRestored(null);setRestored(await chatRequest("chat.backup.restorePreview",{backupId,restoreId:id,passphrase:secret}));
     }
   }catch(e){setError(chatError(e)+" Check the recorded operation ID and local folder before another attempt.");}
   finally{lock.current=false;setBusy(false);}
 }
 return <section className="system-center-option" aria-label="Portable chat vault backup and restore">
   <h3>Encrypted portable chat vault backup</h3>
   <p>Back up saved vault records, managed linked files and published conversation exports. Credentials, model files, logs, caches, unlinked files and old backups are excluded. Maximum archive payload: 64 MiB. Larger data fails without truncation.</p>
   <p>Destination: application data / backups / portable. Keep a copy on a separate disk and store the passphrase safely. Lost passphrases cannot be recovered. A same-disk copy cannot protect against disk failure.</p>
   <label className="help-tool-field"><span>Backup passphrase (at least 12 UTF-8 bytes)</span><input type="password" aria-label="Backup passphrase" autoComplete="new-password" maxLength={1024} disabled={!ready} value={password} onChange={e=>setPassword(e.target.value)}/></label>
   <label className="help-tool-field"><span>Confirm passphrase for creation</span><input type="password" aria-label="Confirm backup passphrase" autoComplete="new-password" maxLength={1024} disabled={!ready} value={confirm} onChange={e=>setConfirm(e.target.value)}/></label>
   <label><input type="checkbox" checked={createConsent} disabled={!ready} onChange={e=>setCreateConsent(e.target.checked)}/> I choose the local portable backup folder and understand recovery requires the passphrase</label>
   <button type="button" className="gold-action" disabled={!ready||!valid||password!==confirm||!createConsent} onClick={()=>void perform("create")}>Create encrypted backup</button>
   {backup&&<div role="group" aria-label="Verified portable backup receipt"><p>Encrypted archive saved and verified · {backup.itemCount} items · {backup.bytes.toLocaleString()} bytes</p><label className="help-tool-field">Backup ID<input readOnly aria-label="Verified backup ID" value={backup.backupId}/></label><label className="help-tool-field">Relative backup path<input readOnly aria-label="Relative backup path" value={backup.relativePath}/></label><p style={{overflowWrap:"anywhere"}}>SHA-256: {backup.sha256}</p></div>}
   <h3>Restore to a separate profile</h3>
   <p>Place a copied .awbackup archive in the local portable folder and enter its filename without the extension. Restore verifies authentication, database integrity and file hashes, then writes a new plaintext profile. It never changes the active vault.</p>
   <label className="help-tool-field"><span>Backup ID to restore</span><input aria-label="Backup ID to restore" maxLength={64} value={backupId} disabled={!ready} onChange={e=>setBackupId(e.target.value)}/></label>
   <label><input type="checkbox" checked={restoreConsent} disabled={!ready} onChange={e=>setRestoreConsent(e.target.checked)}/> I understand restore creates a separate plaintext profile without replacing active data</label>
   <button type="button" className="subtle-action" disabled={!ready||!valid||!restoreConsent||!/^[A-Za-z0-9-]{16,64}$/.test(backupId)} onClick={()=>void perform("restore")}>Verify and restore to new profile</button>
   {restored&&<div role="group" aria-label="Verified restored profile"><p>Verified new profile · {restored.conversationCount} conversations · {restored.itemCount} items. Active profile unchanged.</p><label className="help-tool-field">Relative restored profile path<input readOnly aria-label="Relative restored profile path" value={restored.relativePath}/></label></div>}
   {busy&&<p role="status">Working locally. Do not close the application while this operation is in progress.</p>}
   {operation&&<p className="help-tool-muted">Operation ID: {operation}</p>}
   {error&&<p role="alert">{error}</p>}
   {!connected&&<p role="status">Native backup service unavailable in preview or offline.</p>}
 </section>;
}
