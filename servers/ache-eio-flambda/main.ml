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

let request_handler _ reqd = Reqd.respond_with_string reqd response text

let error_handler _ ?request:_ _ start_response =
  Body.Writer.close (start_response Headers.empty)

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some p -> int_of_string p | None -> 8080
  in
  Eio_main.run @@ fun env ->
  Eio.Switch.run @@ fun sw ->
  let socket =
    Eio.Net.listen ~reuse_addr:true ~backlog:1024 ~sw (Eio.Stdenv.net env)
      (`Tcp (Eio.Net.Ipaddr.V4.any, port))
  in
  let connection_handler =
    Ache_eio.Server.create_connection_handler ~request_handler ~error_handler
  in
  Printf.printf "ache-eio listening on port %d\n%!" port;
  Eio.Net.run_server socket
    ~on_error:(fun exn -> prerr_endline (Printexc.to_string exn))
    (fun flow addr ->
      Eio.Net.setsockopt flow Eio.Net.Sockopt.TCP_NODELAY true;
      connection_handler flow addr)
