(* Hello-world server on httpcats (miou runtime, from robur-coop).

   httpcats serves http/1.1 as [`V1] (an [H1.Reqd.t]) and h2-over-TLS as
   [`V2]; this cleartext server only ever sees [`V1]. The server API is
   young — if your httpcats version differs, adjust the [handler] shape. *)

let text = "Hello, World!"

let handler _flow _conn reqd =
  match reqd with
  | `V2 _ -> assert false (* h2 requires TLS; this server is cleartext *)
  | `V1 reqd ->
      let open H1 in
      let headers =
        Headers.of_list
          [
            ("content-length", string_of_int (String.length text));
            ("content-type", "text/plain");
          ]
      in
      Reqd.respond_with_string reqd (Response.create ~headers `OK) text

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some p -> int_of_string p | None -> 8080
  in
  let sockaddr = Unix.(ADDR_INET (inet_addr_any, port)) in
  Miou_unix.run ~domains:0 @@ fun () ->
  Printf.printf "httpcats listening on port %d\n%!" port;
  Httpcats.Server.clear ~parallel:false ~handler (Httpcats.Server.Bind sockaddr)
