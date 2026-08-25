(* Hello-world server on http/af with the lwt_unix runtime. *)

open Httpaf

let text = "Hello, World!"

let headers =
  Headers.of_list
    [
      ("content-length", string_of_int (String.length text));
      ("content-type", "text/plain");
    ]

let request_handler (_ : Unix.sockaddr) reqd =
  Reqd.respond_with_string reqd (Response.create ~headers `OK) text

let error_handler (_ : Unix.sockaddr) ?request:_ error start_response =
  let response_body = start_response Headers.empty in
  (match error with
  | `Exn exn -> Body.write_string response_body (Printexc.to_string exn)
  | #Status.standard as error ->
      Body.write_string response_body (Status.default_reason_phrase error));
  Body.close_writer response_body

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some p -> int_of_string p | None -> 8080
  in
  let listen_address = Unix.(ADDR_INET (inet_addr_any, port)) in
  Lwt.async (fun () ->
      let open Lwt.Infix in
      Lwt_io.establish_server_with_client_socket listen_address
        (Httpaf_lwt_unix.Server.create_connection_handler ~request_handler
           ~error_handler)
      >>= fun _server ->
      Printf.printf "httpaf listening on port %d\n%!" port;
      Lwt.return_unit);
  let forever, _ = Lwt.wait () in
  Lwt_main.run forever
