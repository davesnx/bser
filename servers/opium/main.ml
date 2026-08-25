open Opium

let text = "Hello, World!"

let hello _request =
  let headers = Headers.of_list [ ("content-length", "13") ] in
  Response.of_plain_text ~headers text |> Lwt.return

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some value -> int_of_string value | None -> 8080
  in
  App.empty
  |> App.host "0.0.0.0"
  |> App.port port
  |> App.jobs 1
  |> App.get "/" hello
  |> App.run_command
