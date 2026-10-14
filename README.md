# bots.oswave.io

Static embed host for Wave bots inside posts (X player cards). Wave Web and Wave OS can't be framed, so embeds live here.

- `/` and anything unknown redirect to https://web.oswave.io/tns/bots.theta
- `/genesis/`: Wave Genesis, an AI inside a Theta contract that dreams a bot from a .theta name, wallet or word
- `/genesis/embed/`: the same page, used as the X player
- `/genesis/x/`: the page you share on X (player card tags)

No backend, no wallet, no keys. Bots are computed by Theta mainnet nodes through a read-only eth_call
(preview mode: the call deploys the model inside a simulation; it switches to the permanent contract once Wave OS deploys it).
