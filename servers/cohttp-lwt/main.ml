open Lwt.Infix

let body = "Hello, World!"

let headers =
  Cohttp.Header.of_list
    [ ("content-type", "text/plain"); ("content-length", "13") ]

let callback _conn _request _request_body =
  Cohttp_lwt_unix.Server.respond_string ~headers ~status:`OK ~body ()

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some value -> int_of_string value | None -> 8080
  in
  let server = Cohttp_lwt_unix.Server.make ~callback () in
  let forever, _ = Lwt.wait () in
  Lwt_main.run
    (Cohttp_lwt_unix.Server.create ~mode:(`TCP (`Port port)) server
    >>= fun () -> forever)
