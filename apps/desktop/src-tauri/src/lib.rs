//! Native transport for P01. No arbitrary filesystem or network IPC commands.
mod ipc;
mod chat_ipc;
mod model_gateway;
mod security;
mod secrets;
mod diagnostics;
mod vault;
mod locations; // native-only; not available to WebView
mod events; // M26 native-only immutable event ledger

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
            // M24 app-owned locations are native-only and cannot move external runtimes.
            let registry = locations::NativeLocationRegistry::open(&os_local, &app_local)
                .map_err(|_| std::io::Error::other("ZYN-STO-001"))?;
            app.manage(registry);
            // Native-only user vault is attached to the OS-owned app data root.
            // Only the bounded M03 chat domain adapter may use it; no raw vault command.
            let storage = vault::NativeVault::open(&app_local)
                .map_err(|_| std::io::Error::other("ZYN-DAT-001"))?;
            app.manage(std::sync::Arc::new(std::sync::Mutex::new(storage)));
            app.manage(model_gateway::LocalModelGateway::new()
                .map_err(|_| std::io::Error::other("ZYN-MODEL-001"))?);
            // M26 event ledger is native-only, never a WebView invoke command.
            let ledger = events::NativeEventLedger::open(&app_local)
                .map_err(|_| std::io::Error::other("ZYN-CHG-001"))?;
            app.manage(std::sync::Mutex::new(ledger));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![ipc::workspace_handshake, chat_ipc::chat_request,
            model_gateway::model_request])
        .run(tauri::generate_context!())
        .expect("ZYN-BOOT-002: unable to initialize native shell");
}
