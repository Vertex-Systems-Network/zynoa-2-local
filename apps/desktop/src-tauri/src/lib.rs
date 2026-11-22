//! Native transport for P01. No arbitrary filesystem or network IPC commands.
mod ipc;
mod security;
mod secrets;
mod diagnostics;
mod vault; // native-only; not available to WebView

use tauri::Manager;

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // Resolve per-user OS paths in native code, not from WebView input.
            let os_local = app.path().local_data_dir()
                .map_err(|_| std::io::Error::other("ZYN-DIAG-001"))?;
            let app_local = app.path().app_local_data_dir()
                .map_err(|_| std::io::Error::other("ZYN-DIAG-001"))?;
            let runtime = diagnostics::NativeDiagnostics::initialize(&os_local, &app_local)
                .map_err(|_| std::io::Error::other("ZYN-DIAG-002"))?;
            runtime.install_redacted_panic_hook();
            app.manage(runtime);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![ipc::workspace_handshake])
        .run(tauri::generate_context!())
        .expect("ZYN-BOOT-002: unable to initialize native shell");
}
