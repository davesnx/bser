(* Hello-world server on httpun with the eio runtime (OCaml 5 effects).
   Written against httpun-eio >= 0.2. *)

open Httpun

let text = "Hello, World!"

let headers =
  Headers.of_list
    [
      ("content-length", string_of_int (String.length text));
      ("content-type", "text/plain");
    ]

let request_handler (_ : Eio.Net.Sockaddr.stream) reqd =
  Reqd.respond_with_string reqd (Response.create ~headers `OK) text

let error_handler (_ : Eio.Net.Sockaddr.stream) ?request:_ error start_response
    =
  let response_body = start_response Headers.empty in
  (match error with
  | `Exn exn -> Body.Writer.write_string response_body (Printexc.to_string exn)
  | #Status.standard as error ->
      Body.Writer.write_string response_body
        (Status.default_reason_phrase error));
  Body.Writer.close response_body

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
    Httpun_eio.Server.create_connection_handler ~request_handler ~error_handler
  in
  Printf.printf "httpun-eio listening on port %d\n%!" port;
  while true do
    Eio.Net.accept_fork socket ~sw
      ~on_error:(fun exn -> prerr_endline (Printexc.to_string exn))
      (fun flow addr -> connection_handler ~sw addr flow)
  done
