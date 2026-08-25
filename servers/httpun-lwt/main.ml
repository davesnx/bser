open Httpun

let body = "Hello, World!"

let headers =
  Headers.of_list [ ("content-type", "text/plain"); ("content-length", "13") ]

let request_handler (_ : Unix.sockaddr) { Gluten.Reqd.reqd; _ } =
  Reqd.respond_with_string reqd (Response.create ~headers `OK) body

let error_handler (_ : Unix.sockaddr) ?request:_ error start_response =
  let response_body = start_response Headers.empty in
  (match error with
  | `Exn exn -> Body.Writer.write_string response_body (Printexc.to_string exn)
  | #Status.standard as status ->
      Body.Writer.write_string response_body (Status.default_reason_phrase status));
  Body.Writer.close response_body

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some value -> int_of_string value | None -> 8080
  in
  let address = Unix.(ADDR_INET (inet_addr_any, port)) in
  let handler =
    Httpun_lwt_unix.Server.create_connection_handler ~request_handler
      ~error_handler
  in
  let forever, _ = Lwt.wait () in
  Lwt_main.run
    (Lwt.bind (Lwt_io.establish_server_with_client_socket address handler)
       (fun _server -> forever))
