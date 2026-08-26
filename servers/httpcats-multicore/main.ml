let text = "Hello, World!"

let handler _flow _conn reqd =
  match reqd with
  | `V2 _ -> assert false
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
  let total_domains =
    match Sys.getenv_opt "BSER_CPU_COUNT" with
    | Some value -> int_of_string value
    | None -> Domain.recommended_domain_count ()
  in
  if total_domains < 2 then invalid_arg "BSER_CPU_COUNT must be at least 2";
  let worker_domains = total_domains - 1 in
  let sockaddr = Unix.(ADDR_INET (inet_addr_any, port)) in
  let serve () =
    Httpcats.Server.clear ~parallel:false ~handler
      (Httpcats.Server.Bind sockaddr)
  in
  Miou_unix.run ~domains:worker_domains @@ fun () ->
  Printf.printf "httpcats listening on port %d with %d domains\n%!" port
    total_domains;
  let primary = Miou.async serve in
  Miou.parallel serve (List.init worker_domains (Fun.const ()))
  |> List.iter (function Ok () -> () | Error exn -> raise exn);
  Miou.await_exn primary
