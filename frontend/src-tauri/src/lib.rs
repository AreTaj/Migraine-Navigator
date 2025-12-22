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
            
            tauri::async_runtime::spawn(async move {
                // ONLY spawn sidecar in Release mode (Packaged App)
                #[cfg(not(debug_assertions))]
                {
                    let (mut rx, mut _child) = handle.shell().sidecar("migraine-navigator-api")
                        .expect("Failed to create sidecar")
                        .spawn()
                        .expect("Failed to spawn sidecar");

                    // CRITICAL: We must keep '_child' alive to keep stdin open.
                    // If this block exits, _child is dropped, stdin closes, and Python self-destructs.
                    // We also listen for events to prevent buffer filling.
                    while let Some(event) = rx.recv().await {
                       // Just consume events
                       // println!("Event: {:?}", event);
                    }
                }
                
                // In Debug/Dev mode, we do nothing here. 
                // The user is expected to run 'uvicorn' manually.
                
                // If event loop ends (sidecar died?), we can exit task.
            });
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

