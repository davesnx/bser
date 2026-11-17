open Ache

let text = "Hello, World!"

let response =
  Response.create
    ~headers:
      (Headers.of_list
         [
           ("content-length", string_of_int (String.length text));
           ("content-type", "text/plain");
         ])
    `OK

let request_handler _ reqd = Request_descriptor.respond_with_string reqd response text

let error_handler _ ?request:_ _ start_response =
  Body.Writer.close (start_response Headers.empty)

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some p -> int_of_string p | None -> 8080
  in
  Sys.set_signal Sys.sigpipe Sys.Signal_ignore;
  let address = Unix.(ADDR_INET (inet_addr_any, port)) in
  let handler =
    Ache_lwt.Server.create_connection_handler ~request_handler ~error_handler
  in
  let forever, _ = Lwt.wait () in
  Lwt_main.run
    (Lwt.bind
       (Lwt_io.establish_server_with_client_socket ~backlog:1024
          ~set_tcp_nodelay:true address handler)
       (fun _server ->
         Printf.printf "ache-lwt listening on port %d\n%!" port;
         forever))
