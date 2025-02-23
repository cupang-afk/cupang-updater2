# Changelog

All notable changes to this project will be documented in this file.

## 0.4.2 - 2025-02-23

### Bug Fixes

- None check for github updater ([9defb3d](9defb3dccd1de0ceb2e101c52b6334ddfd784fdd))

### Bump

- Version 0.4.1 -> 0.4.2 ([]())

## 0.4.1 - 2025-02-23

[830c5e9](830c5e921c5cce53015a3e8df59cd8c3ecb0a9f5)...[b0fb6b3](b0fb6b34f932fb0ed202a683034ee66dea881407)

### Bug Fixes

- Fix list indicies must be integers while using github updater ([b121584](b121584c9f541e4e9a0431dad1bb8a04caf087c9))

### Bump

- Version 0.4.0 -> 0.4.1 ([b0fb6b3](b0fb6b34f932fb0ed202a683034ee66dea881407))

## 0.4.0 - 2025-02-23

[5dbe5a0](5dbe5a0402cf904280042c263f8d039350990ba3)...[830c5e9](830c5e921c5cce53015a3e8df59cd8c3ecb0a9f5)

### Bug Fixes

- Increase make_requests timeout ([2de54c4](2de54c4241215696a6576cc97f7a6cd492e309cf))
- Show which updater in download progress ([01096b9](01096b93d47aa0dc050996878aaa887e70600966))
- Use dirty_load to allow nasty json form in config yaml ([227904a](227904a3d45ec5a6a5a8cd9a4f75810d868111df))
- Register LeafMC and SpigotMC server updater ([243c8ac](243c8ac1a77bcd2b2e915d31efb68ef18c42c0a4))

### Features

- Rewrote GithubAPI ([4e1cb48](4e1cb4815e61fd4bc56c5c653abe969bb459136d))
- Rewrote JenkinsAPI, update BungeeCord updater to respect server.version ([772dd3e](772dd3eaf494d9a3b8543ed76d33ba1ba89e4b4d))
- Add SpigotMC server updater ([9081f8a](9081f8ac7328ad1811ff2a6660eb681f7346441a))
- Add LeafMC server updater ([7738f35](7738f35ac73486761c7498904c6670d9693f8b2d))

### Bump

- Version 0.3.2 -> 0.4.0 ([830c5e9](830c5e921c5cce53015a3e8df59cd8c3ecb0a9f5))

## 0.3.2 - 2025-01-27

[cf2cd93](cf2cd93e8e27f163bc66ea54886f86972dab7f8a)...[5dbe5a0](5dbe5a0402cf904280042c263f8d039350990ba3)

### Bug Fixes

- Log ([8837099](8837099098f457418f2d89af4228fdee7f9006fb))

### Bump

- Version 0.3.1 -> 0.3.2 ([5dbe5a0](5dbe5a0402cf904280042c263f8d039350990ba3))

## 0.3.1 - 2024-12-18

[6ff6ea9](6ff6ea9c20ad86afaac79f3db931f9133176ed6d)...[cf2cd93](cf2cd93e8e27f163bc66ea54886f86972dab7f8a)

### Bug Fixes

- Normalize plugin authors ([8439b80](8439b805db49074268a419f74352f488eb03dfbe))

### Bump

- Version 0.3.0 -> 0.3.1 ([cf2cd93](cf2cd93e8e27f163bc66ea54886f86972dab7f8a))

## 0.3.0 - 2024-12-18

[13bf527](13bf5272236d2544bd14fa61631631ca22ff298e)...[6ff6ea9](6ff6ea9c20ad86afaac79f3db931f9133176ed6d)

### Bug Fixes

- Fix config path point to wrong file path when `--config-dir` is set ([9ef25d3](9ef25d3e06b51f73e631c867017640e62608ac56))
- Fix logger type when error is raised while calling make_requests ([74ebd45](74ebd457f97a53b5e348e0c3ec14748636a667d3))
- Fix jenkins fallback build number when request is fail ([6927d58](6927d58e98b5d162143852ef07cd0a18538f8e2b))
- Debug command arguments ([88cce15](88cce15729c19972e4376e66b42ce2c759bdded4))
- Fix raised error after download is finished ([7bc1748](7bc17487d1b354efda1dbffa42e1d0ddad83299b))

### Features

- Add download retry ([5a74395](5a74395f1151c84feaa068df9eca66c933e5e0e6))
- Add `--skip-version-check` when updating ([b1394da](b1394dad371fa0f6185d2daa0d52686f8b2f5464))

### Performance

- Make Paper update request few small data instead one big data and do sorting ([ba8d6fe](ba8d6fe574bbc749f7cd59907268d592a805e785))

### Refactor

- Setup ruff rules and refactor ([71d77c1](71d77c1f264d66b4367fb84df6561f3d6ec7d807))

### Bump

- Version 0.2.3 -> 0.3.0 ([6ff6ea9](6ff6ea9c20ad86afaac79f3db931f9133176ed6d))

## 0.2.3 - 2024-12-02

[bedff0e](bedff0ee397298ea9e8bd71c36f9854caea0a741)...[13bf527](13bf5272236d2544bd14fa61631631ca22ff298e)

### Bug Fixes

- Fix jar check on bungee plugin ([5ebc230](5ebc23055894e93cdceedf2ea1eaa8aa9da1feb5))

### Bump

- Version 0.2.2 -> 0.2.3 ([13bf527](13bf5272236d2544bd14fa61631631ca22ff298e))

## 0.2.2 - 2024-11-22

[5d88578](5d88578d2a68c45ac0bbcd02f464ca7ae645e222)...[bedff0e](bedff0ee397298ea9e8bd71c36f9854caea0a741)

### Bug Fixes

- Ensure correct log file grouping by date ([11b758f](11b758f554d24db1d0e9d52929975333cac2fa10))

### Bump

- Version 0.2.1 -> 0.2.2 ([bedff0e](bedff0ee397298ea9e8bd71c36f9854caea0a741))

## 0.2.1 - 2024-11-22

[7160b66](7160b66723113095c476129940c977c4a687d3b7)...[5d88578](5d88578d2a68c45ac0bbcd02f464ca7ae645e222)

### Bug Fixes

- Prevent direct calls to _load_ext function ([82f559c](82f559cfaa39e2e4915c385dd20c9e59419d9b6a))
- Fix compress logs not working properly ([bf70bf0](bf70bf0111b922c576ebe278febb92812ed723a5))

### Documentation

- Update `README.md` ([c65c766](c65c766c0246c58d404bc3ba5f895a5d9f3d4dd7))

### Refactor

- Refactor command-line options ([f1230c8](f1230c873e9f293c285da40fe5f0f78ffb661754))

### Bump

- Version 0.2.0 -> 0.2.1 ([5d88578](5d88578d2a68c45ac0bbcd02f464ca7ae645e222))

## 0.2.0 - 2024-11-21

[6663af2](6663af2d4514fb87a9d71e9b4f547034c01d3fd7)...[7160b66](7160b66723113095c476129940c977c4a687d3b7)

### Bug Fixes

- Fix a typo ([fdb7474](fdb74744fcc9516ba3e62ee2a8c3dd43a9e40466))
- Fix SFTP and FTP copy() method ([791aab0](791aab0706349cb7a33fdd89a98ed6ff6f4ce8d5))
- Fix plugins directory is missing check on remote storage ([5ec0560](5ec05601230218b614f3e3fc75cdf91dc27e5417))

### Features

- Add SMB (Samba) support ([1eb6fc1](1eb6fc1980d0618d0acc9b0b5dbee6d54ffc4f1f))
- Add Webdav support ([d147fa7](d147fa7e1d0146d4ad31be5b4d9b550eb7bdf35c))

### Miscellaneous Tasks

- Improve FTP and SFTP copy method ([2da948c](2da948c98a7bfdda8ac2909841cce8e02afb51bd))

### Bump

- Version 0.1.3 -> 0.2.0 ([7160b66](7160b66723113095c476129940c977c4a687d3b7))

## 0.1.3 - 2024-11-20

[6b1ba76](6b1ba7693a054d4a74fc3a95c1f955ba360e47e6)...[6663af2](6663af2d4514fb87a9d71e9b4f547034c01d3fd7)

### Bug Fixes

- Make spigot premium plugin check after new version check ([940abae](940abae8b5e8caa50b80fec32cf0d8986cc7e870))

### Bump

- Version 0.1.2 -> 0.1.3 ([6663af2](6663af2d4514fb87a9d71e9b4f547034c01d3fd7))

## 0.1.2 - 2024-11-18

[bc37080](bc37080a222e6f1b5bce4e959c651ac5c1da83fa)...[6b1ba76](6b1ba7693a054d4a74fc3a95c1f955ba360e47e6)

### Bug Fixes

- I somewhat stupid making stop_event set while scanning which is not good ([82b0c8b](82b0c8b2d4ba1f5ec76bc03060cec087262b171d))

### Bump

- Version 0.1.1 -> 0.1.2 ([6b1ba76](6b1ba7693a054d4a74fc3a95c1f955ba360e47e6))

## 0.1.1 - 2024-11-16

[9518cef](9518cef28df5673a6244c509bf35568665fee761)...[bc37080](bc37080a222e6f1b5bce4e959c651ac5c1da83fa)

### Bug Fixes

- Scanning FileHash error when jar is renamed ([c6f2ec3](c6f2ec355de137fae496a34c3057937ae021bb09))

### Bump

- Version 0.1.0 -> 0.1.1 ([bc37080](bc37080a222e6f1b5bce4e959c651ac5c1da83fa))

## 0.1.0 - 2024-11-16

[1ab8df2](1ab8df213797651bc9badc6f4f75fd366f936a2a)...[9518cef](9518cef28df5673a6244c509bf35568665fee761)

### Bug Fixes

- Fix server and plugin hash not always available ([1bb5e8e](1bb5e8e1c987953feac4e18258e267a642d1463d))
- Fix server build_number get empty when server.jar is not present ([6e8a3ee](6e8a3eebec60d9a96108fe06d50951e20562cf2b))
- Fix plugin_name not always correct ([13f3adf](13f3adf1c7e386265e785b7176badf777ef606b6))

### Features

- Rename plugin.jar when scanning based on plugin metadata ([c90c513](c90c513c0cc8fc386693422eec214879d19a0c56))
- Add SFTP and FTP support ([e6dbaa3](e6dbaa30bf0c8f9581aef389f615cf520b44bb96))
- Add --parallel-downloads option for concurrent downloads ([218fd41](218fd41b00713f703d56c476d2b4e604e6d644b4))

### Miscellaneous Tasks

- Simplify the updater ([5786845](5786845785e36eeaa3a48d55b1651510c9d28297))
- Handle old plugin delete inside update_plugin instead of handler ([ac02094](ac020941995c3485adfc5c16d1562798c6db9d2c))
- Add file stream support to get_jar_info ([7327635](7327635a49b7667fe987a831bee71879e270c1bd))

### Bump

- Version 0.0.2 -> 0.1.0 ([9518cef](9518cef28df5673a6244c509bf35568665fee761))

## 0.0.2 - 2024-11-09

[59207a7](59207a70a58a8d7bec6f28e7b53000ecf857ed7f)...[1ab8df2](1ab8df213797651bc9badc6f4f75fd366f936a2a)

### Bug Fixes

- `packaging` library not included as dependencies ([7360b8c](7360b8c57df5ca02640c8a561a181a9fc8844db8))
- Settings.update_order not generated at first run ([891298f](891298f9840befc19311da08382802052cf98fdb))
- Minor fix for plugin updater related to version ([523fcc6](523fcc6111ce60c1eb66b480f4b11db68db91675))

### Documentation

- Update related to docs ([2c42619](2c426192f1144456891e4797e7613e96c2147188))

### Miscellaneous Tasks

- Update `README.md` ([5077405](50774058e542fc08a186db85d7bdc774925877b8))
- Add log.info when loading config ([dec5f0b](dec5f0bec7cc404d7d81477eb1859ccc713e1d28))
- Add log.info when loading config ([879bb84](879bb845000f00b98d5e76b23392acc9391faa4e))

### Bump

- Version 0.0.1 -> 0.0.2 ([1ab8df2](1ab8df213797651bc9badc6f4f75fd366f936a2a))

## 0.0.1 - 2024-11-09

### Documentation

- Update mkdocs ([27c9e24](27c9e24ad0bd7dd43cac3db30288b409133d7058))

### Features

- Well, this is actually full code in one commit ([0ec0a16](0ec0a16c44fd4a6c181adf6a012658ca16766f92))

### Miscellaneous Tasks

- Update `.gitignore` ([092e7d6](092e7d62974895c75aa293857adf48e74308972c))
- Update `.gitignore` ([b2d758e](b2d758e3f9419bcdce8260f89fc4e45e49d993c0))
- Update `README.md` ([afa5773](afa577371600f8c9771130f01a2bc2c4758ed2ce))

### Bump

- Version - -> 0.0.1 ([59207a7](59207a70a58a8d7bec6f28e7b53000ecf857ed7f))

<!-- generated by git-cliff -->
