let text = Riot.Bytestring.of_string "Hello, World!"

let endpoint =
  let open Trail in
  let open Router in
  [
    router
      [
        get "/" (fun conn ->
            conn
            |> Conn.with_header "content-type" "text/plain"
            |> Conn.with_header "content-length" "13"
            |> Conn.send_response `OK text);
      ];
  ]

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some value -> int_of_string value | None -> 8080
  in
  Riot.run ~workers:0 @@ fun () ->
  let handler = Nomad.trail endpoint in
  let pid = Nomad.start_link ~acceptors:1 ~port ~handler () |> Result.get_ok in
  Riot.wait_pids [ pid ]
