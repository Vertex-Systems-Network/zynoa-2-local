//! Native transport for P01. No filesystem, user data writes or network commands.
mod ipc;
mod security;
mod secrets;
mod diagnostics; // native-only, no IPC

pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![ipc::workspace_handshake])
        .run(tauri::generate_context!())
        .expect("ZYN-BOOT-002: unable to initialize native shell");
}
