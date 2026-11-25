fn main() {
    // Custom application commands are denied unless explicitly granted.
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&[
                "workspace_handshake", "chat_request", "model_request"
            ])),
    )
    .expect("ZYN-IPC-BUILD: unable to generate least-privilege command manifest");
}
