//! P03 T12–T14 fail-closed backup/recovery contracts.
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BackupEnvelope { pub version: u8, pub nonce: String, pub ciphertext_sha256: String, pub key_ref: String }

pub fn envelope(version: u8, nonce: &str, ciphertext: &[u8], key_ref: &str) -> Option<BackupEnvelope> {
    if version != 1 || nonce.len() < 16 || nonce.len() > 64 || key_ref.is_empty() || key_ref.len() > 128
        || !key_ref.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_') || ciphertext.is_empty() { return None; }
    let mut h = Sha256::new(); h.update(ciphertext);
    Some(BackupEnvelope { version, nonce: nonce.to_owned(), ciphertext_sha256: format!("{:x}", h.finalize()), key_ref: key_ref.to_owned() })
}
pub fn verify_envelope(meta: &BackupEnvelope, ciphertext: &[u8]) -> bool { envelope(meta.version, &meta.nonce, ciphertext, &meta.key_ref).is_some_and(|x| x == *meta) }
/// Lexical staging target only; no file is opened or written here.
pub fn staged_restore_target(path: &str) -> Option<String> {
    if !crate::artifact_contracts::valid_managed_basename(path) { return None; }
    Some(format!("restore-staging/{path}"))
}
pub fn performance_budget_ms(cold: u64, warm: &[u64]) -> bool { cold <= 15_000 && !warm.is_empty() && warm.iter().all(|x| *x <= 2_000) }

#[cfg(test)]
mod tests { use super::*;
    #[test]
    fn restore_targets_use_the_same_portable_name_policy() {
        for name in ["", ".", "..", "file:stream", "nul.txt", "LPT³.log", "name.", "name ",
            "a\nb", "a/b", "a\\b", "bad?.bin"] {
            assert!(staged_restore_target(name).is_none(), "{name:?}");
        }
        assert!(staged_restore_target(&"a".repeat(161)).is_none());
        assert_eq!(staged_restore_target("备份.bin").as_deref(), Some("restore-staging/备份.bin"));
    }
    #[test] fn encrypted_backup_is_integrity_bound_and_staged() { let e=envelope(1,"0123456789abcdef",b"ciphertext","os-key-01").unwrap(); assert!(verify_envelope(&e,b"ciphertext")); assert!(!verify_envelope(&e,b"plain")); assert_eq!(staged_restore_target("snapshot.bin").as_deref(),Some("restore-staging/snapshot.bin")); assert!(staged_restore_target("../db").is_none()); }
    #[test] fn budget_is_bounded() { assert!(performance_budget_ms(1000,&[100,200])); assert!(!performance_budget_ms(16000,&[100])); }
}

// Portable v1 cryptography and binary manifest. The header is authenticated
// as AAD. No password or plaintext may be logged. Never use the older
// hash-only envelope as an encryption or authentication substitute.
use argon2::{Algorithm,Argon2,Block,Params,Version};
use ring::{aead,rand::{SecureRandom,SystemRandom}};
use serde::{Deserialize,Serialize};
use zeroize::Zeroizing;

pub(crate) const MAX_PORTABLE_BYTES:usize=64*1024*1024;
const MAX_MANIFEST_BYTES:usize=2*1024*1024;
const MAX_ITEMS:usize=4096;
const MAGIC:&[u8;8]=b"ZYNAWB01";
const HEADER:usize=8+16+12+8;
const TAG:usize=16;
const KDF_MEMORY:u32=64*1024;
const KDF_ITERATIONS:u32=3;

#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub(crate) enum PortableFault { Invalid, Authentication, Storage }

pub(crate) fn valid_backup_passphrase(passphrase:&[u8])->bool{
    (12..=1024).contains(&passphrase.len())&&!passphrase.contains(&0)
}
fn key(passphrase:&[u8],salt:&[u8])->Result<aead::LessSafeKey,PortableFault>{
    if !valid_backup_passphrase(passphrase)||salt.len()!=16{return Err(PortableFault::Invalid);}
    let params=Params::new(KDF_MEMORY,KDF_ITERATIONS,1,Some(32)).map_err(|_|PortableFault::Invalid)?;
    let mut blocks=Zeroizing::new(Vec::<Block>::new());
    blocks.try_reserve_exact(KDF_MEMORY as usize).map_err(|_|PortableFault::Storage)?;
    blocks.resize(KDF_MEMORY as usize,Block::default());
    let mut derived=Zeroizing::new([0u8;32]);
    Argon2::new(Algorithm::Argon2id,Version::V0x13,params)
        .hash_password_into_with_memory(passphrase,salt,&mut *derived,&mut **blocks)
        .map_err(|_|PortableFault::Authentication)?;
    let key=aead::UnboundKey::new(&aead::AES_256_GCM,&*derived).map_err(|_|PortableFault::Authentication)?;
    Ok(aead::LessSafeKey::new(key))
}
pub(crate) fn seal_portable(plain:Zeroizing<Vec<u8>>,passphrase:&[u8])->Result<Vec<u8>,PortableFault>{
    if plain.is_empty()||plain.len()>MAX_PORTABLE_BYTES||!valid_backup_passphrase(passphrase){return Err(PortableFault::Invalid);}
    let mut salt=[0u8;16];let mut nonce=[0u8;12];
    let rng=SystemRandom::new();
    rng.fill(&mut salt).map_err(|_|PortableFault::Storage)?;
    rng.fill(&mut nonce).map_err(|_|PortableFault::Storage)?;
    let mut header=Vec::with_capacity(HEADER);
    header.extend_from_slice(MAGIC);header.extend_from_slice(&salt);header.extend_from_slice(&nonce);
    header.extend_from_slice(&(plain.len() as u64).to_le_bytes());
    let key=key(passphrase,&salt)?;
    let mut cipher=plain;
    key.seal_in_place_append_tag(aead::Nonce::assume_unique_for_key(nonce),aead::Aad::from(&header),&mut *cipher)
        .map_err(|_|PortableFault::Authentication)?;
    header.extend_from_slice(&cipher);
    Ok(header)
}
pub(crate) fn open_portable(archive:&[u8],passphrase:&[u8])->Result<Zeroizing<Vec<u8>>,PortableFault>{
    if archive.len()<HEADER+TAG+1||archive.len()>HEADER+TAG+MAX_PORTABLE_BYTES||&archive[..8]!=MAGIC{
        return Err(PortableFault::Invalid);
    }
    let length=u64::from_le_bytes(archive[36..44].try_into().map_err(|_|PortableFault::Invalid)?);
    if length==0||length>MAX_PORTABLE_BYTES as u64||archive.len()!=HEADER+TAG+length as usize{
        return Err(PortableFault::Invalid);
    }
    let nonce:[u8;12]=archive[24..36].try_into().map_err(|_|PortableFault::Invalid)?;
    let key=key(passphrase,&archive[8..24])?;
    let mut plaintext=Zeroizing::new(archive[HEADER..].to_vec());
    let opened=key.open_in_place(aead::Nonce::assume_unique_for_key(nonce),aead::Aad::from(&archive[..HEADER]),&mut *plaintext)
        .map_err(|_|PortableFault::Authentication)?.len();
    if opened!=length as usize{return Err(PortableFault::Authentication);}
    plaintext.truncate(opened);
    Ok(plaintext)
}

#[derive(Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields,rename_all="camelCase")]
pub(crate) struct PortableItem {pub(crate) kind:String,pub(crate) id:String,pub(crate) offset:u64,pub(crate) bytes:u64,pub(crate) sha256:String}
#[derive(Serialize,Deserialize)]
#[serde(deny_unknown_fields,rename_all="camelCase")]
struct PortableManifest {format_version:u8,schema_version:i64,app_version:String,created_at:u64,
    scope:String,encryption:String,compression:String,included:Vec<String>,excluded:Vec<String>,items:Vec<PortableItem>}

fn included()->Vec<String>{["vault","managed-linked-files","published-conversation-exports"].iter().map(|x|x.to_string()).collect()}
fn excluded()->Vec<String>{["credentials","models","logs","caches","external-files","unlinked-blobs","stages","previous-backups"].iter().map(|x|x.to_string()).collect()}
fn sha(bytes:&[u8])->String{format!("{:x}",Sha256::digest(bytes))}
fn hash_valid(s:&str)->bool{s.len()==64&&s.bytes().all(|b|b.is_ascii_digit()||(b'a'..=b'f').contains(&b))}
pub(crate) fn valid_export_filename(s:&str)->bool{
    s.strip_prefix("conversation-").and_then(|s|s.strip_suffix(".json")).is_some_and(|s|
        (8..=64).contains(&s.len())&&s.bytes().all(|b|b.is_ascii_alphanumeric()||b==b'_'||b==b'-'))
}
fn valid_item(kind:&str,id:&str,bytes:u64)->bool{
    match kind {
        "database"=>id=="state.sqlite"&&bytes>0,
        "blob"=>hash_valid(id)&&bytes<=crate::artifact_contracts::MAX_ATTACHMENT,
        "export"=>valid_export_filename(id)&&bytes>0&&bytes<=32*1024*1024,
        _=>false,
    }
}
pub(crate) struct PortableBuilder {items:Vec<PortableItem>,data:Zeroizing<Vec<u8>>}
impl PortableBuilder {
    pub(crate) fn new()->Self{Self{items:Vec::new(),data:Zeroizing::new(Vec::new())}}
    pub(crate) fn add(&mut self,kind:&str,id:&str,bytes:&[u8])->Result<(),PortableFault>{
        if !valid_item(kind,id,bytes.len() as u64)||self.items.len()>=MAX_ITEMS||
            self.data.len().checked_add(bytes.len()).filter(|n|*n<=MAX_PORTABLE_BYTES).is_none()||
            self.items.iter().any(|x|x.kind==kind&&x.id.eq_ignore_ascii_case(id)){return Err(PortableFault::Invalid);}
        let hash=sha(bytes);
        if kind=="blob"&&hash!=id{return Err(PortableFault::Invalid);}
        self.items.push(PortableItem{kind:kind.into(),id:id.into(),offset:self.data.len() as u64,bytes:bytes.len() as u64,sha256:hash});
        self.data.extend_from_slice(bytes);Ok(())
    }
    pub(crate) fn finish(self,created_at:u64)->Result<Zeroizing<Vec<u8>>,PortableFault>{
        if created_at==0||self.items.first().map(|x|x.kind.as_str())!=Some("database"){return Err(PortableFault::Invalid);}
        let manifest=PortableManifest{format_version:1,schema_version:4,app_version:env!("CARGO_PKG_VERSION").into(),
            created_at,scope:"local-chat-vault".into(),encryption:"argon2id-v19-m65536-t3-p1-aes256gcm".into(),
            compression:"none".into(),included:included(),excluded:excluded(),items:self.items};
        let json=serde_json::to_vec(&manifest).map_err(|_|PortableFault::Invalid)?;
        if json.len()>MAX_MANIFEST_BYTES||4+json.len()+self.data.len()>MAX_PORTABLE_BYTES{return Err(PortableFault::Invalid);}
        let mut out=Zeroizing::new(Vec::with_capacity(4+json.len()+self.data.len()));
        out.extend_from_slice(&(json.len() as u32).to_le_bytes());out.extend_from_slice(&json);out.extend_from_slice(&self.data);
        Ok(out)
    }
}
/// Verify all offsets, allowed logical IDs and hashes before any restore write.
pub(crate) fn unpack_portable(plain:&[u8])->Result<Vec<(PortableItem,&[u8])>,PortableFault>{
    if plain.len()<5||plain.len()>MAX_PORTABLE_BYTES{return Err(PortableFault::Invalid);}
    let n=u32::from_le_bytes(plain[..4].try_into().map_err(|_|PortableFault::Invalid)?) as usize;
    if n==0||n>MAX_MANIFEST_BYTES||4+n>plain.len(){return Err(PortableFault::Invalid);}
    let m:PortableManifest=serde_json::from_slice(&plain[4..4+n]).map_err(|_|PortableFault::Invalid)?;
    if m.format_version!=1||m.schema_version!=4||m.app_version!=env!("CARGO_PKG_VERSION")||m.created_at==0||
        m.scope!="local-chat-vault"||m.encryption!="argon2id-v19-m65536-t3-p1-aes256gcm"||m.compression!="none"||
        m.included!=included()||m.excluded!=excluded()||m.items.is_empty()||m.items.len()>MAX_ITEMS||
        m.items[0].kind!="database"{return Err(PortableFault::Invalid);}
    let data=&plain[4+n..];let mut at=0usize;let mut seen=std::collections::HashSet::new();let mut out=Vec::new();
    for item in m.items{
        if !valid_item(&item.kind,&item.id,item.bytes)||item.offset!=at as u64||
            !seen.insert((item.kind.clone(),item.id.to_ascii_lowercase()))||!hash_valid(&item.sha256)||
            item.bytes>MAX_PORTABLE_BYTES as u64{return Err(PortableFault::Invalid);}
        let end=at.checked_add(item.bytes as usize).filter(|n|*n<=data.len()).ok_or(PortableFault::Invalid)?;
        let bytes=&data[at..end];
        if sha(bytes)!=item.sha256||(item.kind=="blob"&&item.sha256!=item.id){return Err(PortableFault::Invalid);}
        out.push((item,bytes));at=end;
    }
    if at!=data.len(){return Err(PortableFault::Invalid);}
    Ok(out)
}

#[cfg(test)]
mod portable_tests {
    use super::*;
    #[test]
    fn actual_aead_roundtrip_rejects_wrong_password_tamper_and_truncation(){
        let password=b"synthetic portable passphrase";
        let mut b=PortableBuilder::new();b.add("database","state.sqlite",b"synthetic private data").unwrap();
        let p=b.finish(1).unwrap();let cipher=seal_portable(p,password).unwrap();
        assert!(!cipher.windows(22).any(|x|x==b"synthetic private data"));
        assert_eq!(unpack_portable(&open_portable(&cipher,password).unwrap()).unwrap()[0].1,b"synthetic private data");
        assert!(matches!(open_portable(&cipher,b"incorrect passphrase"),Err(PortableFault::Authentication)));
        let mut tampered=cipher.clone();let end=tampered.len()-1;tampered[end]^=1;
        assert!(matches!(open_portable(&tampered,password),Err(PortableFault::Authentication)));
        assert!(open_portable(&cipher[..cipher.len()-1],password).is_err());
        let mut header=cipher.clone();header[8]^=1;
        assert!(open_portable(&header,password).is_err());
        assert!(seal_portable(Zeroizing::new(vec![1]),b"short").is_err());
    }
    #[test]
    fn portable_unpack_rejects_authenticated_but_invalid_manifest_structure(){
        let mut builder=PortableBuilder::new();
        builder.add("database","state.sqlite",b"db").unwrap();
        builder.add("export","conversation-AbCd1234.json",b"one").unwrap();
        builder.add("export","conversation-EfGh5678.json",b"two").unwrap();
        let plain=builder.finish(1).unwrap();
        let size=u32::from_le_bytes(plain[..4].try_into().unwrap()) as usize;
        let original:serde_json::Value=serde_json::from_slice(&plain[4..4+size]).unwrap();
        let bytes=&plain[4+size..];
        let encode=|manifest:&serde_json::Value|{
            let json=serde_json::to_vec(manifest).unwrap();
            let mut data=(json.len() as u32).to_le_bytes().to_vec();
            data.extend_from_slice(&json);
            data.extend_from_slice(bytes);
            data
        };
        assert_eq!(unpack_portable(&encode(&original)).unwrap().len(),3);
        let mut bad=original.clone();
        bad["items"][2]["id"]=serde_json::json!("conversation-abcd1234.json");
        assert!(unpack_portable(&encode(&bad)).is_err());
        let mut bad=original.clone();
        bad["items"][1]["id"]=serde_json::json!("../outside.json");
        assert!(unpack_portable(&encode(&bad)).is_err());
        let mut bad=original.clone();
        bad["items"][1]["offset"]=serde_json::json!(0);
        assert!(unpack_portable(&encode(&bad)).is_err());
        let mut bad=original.clone();
        bad["items"][1]["bytes"]=serde_json::json!(u64::MAX);
        assert!(unpack_portable(&encode(&bad)).is_err());
        let mut bad=original.clone();
        bad["items"][1]["path"]=serde_json::json!("external");
        assert!(unpack_portable(&encode(&bad)).is_err());
        let mut trailing=encode(&original);
        trailing.push(0);
        assert!(unpack_portable(&trailing).is_err());
        // AEAD authenticity is necessary, not sufficient: a valid-key
        // archive containing a malformed manifest still fails validation.
        let mut bad=original.clone();
        bad["items"][2]["id"]=serde_json::json!("conversation-abcd1234.json");
        let pass=b"synthetic portable passphrase";
        let encrypted=seal_portable(Zeroizing::new(encode(&bad)),pass).unwrap();
        let decrypted=open_portable(&encrypted,pass).unwrap();
        assert!(unpack_portable(&decrypted).is_err());
    }

    #[test]
    fn portable_manifest_refuses_escape_duplicate_and_modified_payload(){
        let mut b=PortableBuilder::new();b.add("database","state.sqlite",b"db").unwrap();
        assert!(b.add("database","state.sqlite",b"db").is_err());
        assert!(b.add("export","../escape.json",b"x").is_err());
        b.add("export","conversation-AbCd1234.json",b"one").unwrap();
        assert!(b.add("export","conversation-abcd1234.json",b"two").is_err());
        assert!(b.add("blob",&"a".repeat(64),b"x").is_err());
        b.add("blob",&sha(b"blob"),b"blob").unwrap();
        let mut p=b.finish(1).unwrap();
        assert_eq!(unpack_portable(&p).unwrap().len(),3);
        let end=p.len()-1;p[end]^=1;
        assert!(unpack_portable(&p).is_err());
    }
}
