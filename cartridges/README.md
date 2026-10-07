# Aura Public Creator Cartridges

**Built with Aura in under half an hour of total work time. $0 external API spend. No provider API calls in the default shipped demos. Lightweight, independently updateable cartridges.**

Live targets (GitHub Pages):
- Arena: https://dallascourchene-commits.github.io/AuraWorldSeed/
- Cartridge Gallery: https://dallascourchene-commits.github.io/AuraWorldSeed/cartridges/
- Astral Cyber-Strike: https://dallascourchene-commits.github.io/AuraWorldSeed/cartridges/game.html
- AuraSonic Voice Studio: https://dallascourchene-commits.github.io/AuraWorldSeed/cartridges/voice.html
- REA + Canonical Atomizer: https://dallascourchene-commits.github.io/AuraWorldSeed/cartridges/atomizer.html
- Aura Focus Reader: https://dallascourchene-commits.github.io/AuraWorldSeed/cartridges/reader.html

The private AuraOS development substrate remains separate. This public repo carries runnable public world/cartridge surfaces.

Architecture: `stable substrate -> mount cartridge -> canary -> use capability -> receipt -> eject/update`

Keepers:
- `Cartridge != Arena`
- `BaseSubstratePreserved`
- `ReuseBeforeInvent`
- `CapabilityCandidate != AtomAdmission != ExecutionAuthority`
- `SceneFirstVideoSecond`
- `ExactArbitraryReconstruction != GuaranteedAlgebraicCompression`
- `NoCredentialsInCartridge`
- `TestBeforePublish`

The compressed cartridge bodies hydrate in-browser with `DecompressionStream`. Provider integrations are adapters only; no provider secret is embedded in the public files.
