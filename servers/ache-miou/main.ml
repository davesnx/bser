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

let rec clean_up orphans =
  match Miou.care orphans with
  | None | Some None -> ()
  | Some (Some prm) ->
      (match Miou.await prm with
      | Ok () -> ()
      | Error exn -> prerr_endline (Printexc.to_string exn));
      clean_up orphans

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some p -> int_of_string p | None -> 8080
  in
  Sys.set_signal Sys.sigpipe Sys.Signal_ignore;
  let handler =
    Ache_miou.Server.create_connection_handler ~request_handler ~error_handler
  in
  Miou_unix.run ~domains:0 @@ fun () ->
  let listening = Miou_unix.tcpv4 () in
  Miou_unix.bind_and_listen ~backlog:1024 listening
    Unix.(ADDR_INET (inet_addr_any, port));
  Printf.printf "ache-miou listening on port %d\n%!" port;
  let rec accept orphans =
    clean_up orphans;
    match Miou_unix.accept listening with
    | exception Unix.Unix_error ((EMFILE | ENFILE), _, _) ->
        Miou.yield ();
        accept orphans
    | socket, addr ->
        (try
           Unix.setsockopt (Miou_unix.to_file_descr socket) Unix.TCP_NODELAY
             true
         with Unix.Unix_error _ -> ());
        ignore
          (Miou.async ~orphans (fun () ->
               Fun.protect
                 ~finally:(fun () -> Miou_unix.close socket)
                 (fun () -> handler socket addr))
            : unit Miou.t);
        accept orphans
  in
  accept (Miou.orphans ())
