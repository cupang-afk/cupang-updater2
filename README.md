A Minecraft Server/Plugin Updater

This is a rewrite of [cupang-updater](https://github.com/cupang-afk/cupang-updater) with a focus on making it easier to implement new features.

### Documentation

The documentation for this project can be found [here](https://cupang-afk.github.io/cupang-updater2).

### Install

```python
pip install git+https://github.com/cupang-afk/cupang-updater2.git#egg=cupang-updater
```

### Usage

```shell
$ cupang-updater
```

Running for the first time creates a `cupang-updater` directory with a `config.yaml` file for configuration. Use `--config-dir` and `--config` to change their locations.

### Custom Updater

To create a custom updater, implement a new class that extends `PluginUpdater` or `ServerUpdater` and register it using `plugin_updater_register` or `server_updater_register`.

Here is an example of a custom plugin updater:

```python
from cupang_updater.updater.plugin.base import PluginUpdater
from cupang_updater.manager.plugin import plugin_updater_register

class MyCustomPluginUpdater(PluginUpdater):
    def get_update(self):
        # Implement your update logic here
        pass

plugin_updater_register(MyCustomPluginUpdater)
```

Place your custom updater script in `cupang-updater/ext_updater` as a `.py` file, and it will be automatically detected.

<details>
<summary>example hangar.py</summary>

```python
import json

import strictyaml as sy

from cupang_updater.updater.base import CommonData
from cupang_updater.updater.plugin.base import PluginUpdater, PluginUpdaterConfig, PluginUpdaterConfigSchema
from cupang_updater.manager.plugin import plugin_updater_register


class PlatformType(sy.Str):
    platform = ["paper", "waterfall", "velocity"]

    def validate_scalar(self, chunk):
        val: str = chunk.contents
        val = val.lower()
        if val not in self.platform:
            chunk.expecting_but_found(f"when expecting one of these: {self.platform}")
        return super().validate_scalar(chunk)


class Channel(sy.Str):
    channel = ["release", "snapshot", "alpha"]

    def validate_scalar(self, chunk):
        val: str = chunk.contents
        if val not in self.channel:
            chunk.expecting_but_found(f"when expecting one of these: {self.channel}")

        return super().validate_scalar(chunk)


class HangarUpdater(PluginUpdater):
    def __init__(self, plugin_data: CommonData, updater_config: PluginUpdaterConfig):
        self.api = "https://hangar.papermc.io/api/v1/projects"
        super().__init__(plugin_data, updater_config)

    @staticmethod
    def get_updater_name():
        return "Hangar"

    @staticmethod
    def get_config_path():
        return "hangar"

    @staticmethod
    def get_updater_version():
        return "1.0"

    @staticmethod
    def get_config_schema():
        return PluginUpdaterConfigSchema(
            plugin_schema=sy.Map(
                {
                    "id": sy.EmptyNone() | sy.Str(),
                    "platform": sy.EmptyNone() | PlatformType(),
                    "channel": Channel(),
                }
            ),
            plugin_default="""\
                # id: example https://hangar.papermc.io/[author]/[your project id here]
                # platform: one of these, paper, waterfall, velocity
                # channel: update channel # release, snapshot, alpha
                id:
                platform: paper
                channel: release
            """,
        )

    def _get_update_data(self, project_id: str, channel: str):
        headers = {"Accept": "text/plain"}
        res = self.make_requests(
            self.make_url(
                self.api, project_id, "latest", channel=channel.lower().capitalize()
            ),
            headers=headers,
        )
        if not self.check_content_type(res, "text/plain"):
            return

        latest_version = res.read().decode().strip()
        headers = {"Accept": "application/json"}
        res = self.make_requests(
            self.make_url(self.api, project_id, "versions", latest_version),
            headers=headers,
        )
        if not self.check_content_type(res, "application/json"):
            return

        return json.loads(res.read())

    def get_update(self) -> CommonData | None:
        project_id: str = self.updater_config.plugin_config["id"]
        if not project_id:
            return
        platform: str = self.updater_config.plugin_config["platform"]
        if not platform:
            return
        channel: str = self.updater_config.plugin_config["channel"]
        if not channel:
            return

        update_data = self._get_update_data(project_id, channel)
        if not update_data:
            return

        # Compare local and remote versions
        local_version = self.parse_version(self.plugin_data.version)
        remote_version = str(update_data["name"])
        if local_version >= self.parse_version(remote_version):
            return

        url = self.make_url(
            self.api,
            project_id,
            "versions",
            update_data["name"],
            platform.upper(),
            "download",
        )
        with self.make_requests(url, method="HEAD") as res:
            if not any(
                self.check_content_type(res, x)
                for x in [
                    "application/java-archive",
                    "application/octet-stream",
                    "application/zip",
                ]
            ):
                self.log.error(
                    f"When checking update for {self.plugin_data.name}, got {url} but its not a file"
                )
                return

        plugin_data = CommonData(
            name=self.plugin_data.name,
            version=remote_version,
        )
        plugin_data.set_url(url)
        return plugin_data

# Register the plugin updater
plugin_updater_register(HangarUpdater)
```

</details>

> [!CAUTION]
> Refer to the implementation in [ext_register](src/cupang_updater/manager/external.py)
>
> This approach is as powerful as using `exec()`, so proceed with caution.


### Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request on GitHub. 

### License

This project is licensed under the GNU General Public License version 3. See the `LICENSE` file for more information.


### TODO

- [ ] Update documentation