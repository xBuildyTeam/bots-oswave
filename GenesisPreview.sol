// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "./WaveGenesis.sol";
/// Preview runner: used only inside a read-only eth_call. It deploys WaveGenesis in the simulated call,
/// dreams one bot and returns the 200-byte half grid + palette byte. Nothing is ever stored on chain.
contract GenesisPreview {
    constructor(bytes memory w, int256 boost, bytes32 seed) {
        WaveGenesis g = new WaveGenesis(w, boost);
        (bytes memory half, uint8 p) = g.dream(seed);
        bytes memory out = abi.encodePacked(half, p);
        assembly { return(add(out, 32), mload(out)) }
    }
}
