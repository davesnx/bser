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
  Sys.set_signal Sys.sigpipe Sys.Signal_ignore;
  Miou_unix.run ~domains:(domains - 1) @@ fun () ->
  Printf.printf "ache-miou-multicore listening on port %d with %d domains\n%!"
    port domains;
  Ache_miou.Server.run ~domains ~backlog:1024
    ~on_error:(fun exn -> prerr_endline (Printexc.to_string exn))
    ~request_handler ~error_handler
    Unix.(ADDR_INET (inet_addr_any, port))
