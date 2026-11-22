//! P01 native bootstrap: no commands or filesystem authority yet.
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("ZYN-BOOT-002: unable to initialize native shell");
}
