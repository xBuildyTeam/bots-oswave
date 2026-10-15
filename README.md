# bots.oswave.io

Static embed host for Wave bots inside posts (X player cards). Wave Web and Wave OS can't be framed, so embeds live here.

- `/`: home page with Wavey and Wave Genesis
- `/wavey/`: chat with Wavey (calls Wave Web's botChat at web.oswave.io; `?bot=name.theta` to point at another bot)
- anything unknown redirects to `/`
- `/genesis/`: Wave Genesis, an AI inside a Theta contract that dreams a bot from a .theta name, wallet or word
- `/genesis/embed/`: the same page, used as the X player
- `/genesis/x/`: the page you share on X (player card tags)

No backend, no wallet, no keys. Bots are computed by Theta mainnet nodes through read-only eth_calls to the Wave Genesis v1 contract 0xfe33d2b4279ec269f4beca499c7a7b704ab54397 (manifest: BrainVault v3 card #53, test vectors #52, recipe #51).
