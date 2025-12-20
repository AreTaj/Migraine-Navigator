// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}


use tauri_plugin_shell::ShellExt;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let handle = app.handle().clone();
            
            // Spawn the sidecar (Python API)
            tauri::async_runtime::spawn(async move {
                let (_rx, _child) = handle.shell().sidecar("migraine-navigator-api")
                    .expect("Failed to create sidecar")
                    .spawn()
                    .expect("Failed to spawn sidecar");

                // Keep the child process alive
                // We can read events here if needed:
                // while let Some(event) = rx.recv().await { ... }
            });
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
