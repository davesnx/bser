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
  let domains =
    match Sys.getenv_opt "BSER_CPU_COUNT" with
    | Some n -> int_of_string n
    | None -> Domain.recommended_domain_count ()
  in
  Eio_main.run @@ fun env ->
  Printf.printf "ache-eio-multicore listening on port %d with %d domains\n%!"
    port domains;
  Ache_eio.Server.run ~domains ~backlog:1024
    ~on_error:(fun exn -> prerr_endline (Printexc.to_string exn))
    ~net:(Eio.Stdenv.net env) ~domain_mgr:(Eio.Stdenv.domain_mgr env)
    ~request_handler ~error_handler
    (`Tcp (Eio.Net.Ipaddr.V4.any, port))
