import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pylauncher import auth, install, launch, rules, versions
from pylauncher.paths import Paths


class RulesTest(unittest.TestCase):
    def test_no_rules_allows(self):
        self.assertTrue(rules.allowed(None))

    def test_os_rules(self):
        with mock.patch("pylauncher.rules.os_name", return_value="linux"):
            self.assertTrue(rules.allowed([{"action": "allow", "os": {"name": "linux"}}]))
            self.assertFalse(rules.allowed([{"action": "allow", "os": {"name": "osx"}}]))
            self.assertFalse(rules.allowed(
                [{"action": "allow"}, {"action": "disallow", "os": {"name": "linux"}}]))

    def test_features(self):
        rule = [{"action": "allow", "features": {"has_custom_resolution": True}}]
        self.assertFalse(rules.allowed(rule, {}))
        self.assertTrue(rules.allowed(rule, {"has_custom_resolution": True}))


class MavenTest(unittest.TestCase):
    def test_paths(self):
        self.assertEqual(install.maven_path("org.ow2.asm:asm:9.6"),
                         "org/ow2/asm/asm/9.6/asm-9.6.jar")
        self.assertEqual(install.maven_path("org.lwjgl:lwjgl:3.3.3:natives-linux"),
                         "org/lwjgl/lwjgl/3.3.3/lwjgl-3.3.3-natives-linux.jar")
        self.assertEqual(install.maven_path("a.b:c:1@zip"), "a/b/c/1/c-1.zip")


class MergeTest(unittest.TestCase):
    def test_child_overrides_parent(self):
        parent = {
            "id": "1.21.1", "mainClass": "vanilla.Main",
            "arguments": {"game": ["--a"], "jvm": ["-Dp"]},
            "libraries": [{"name": "org.ow2.asm:asm:9.3"},
                          {"name": "org.lwjgl:lwjgl:3.3.3"},
                          {"name": "org.lwjgl:lwjgl:3.3.3:natives-linux"}],
        }
        child = {
            "id": "fabric", "inheritsFrom": "1.21.1", "mainClass": "fabric.Main",
            "arguments": {"game": [], "jvm": ["-Dc"]},
            "libraries": [{"name": "org.ow2.asm:asm:9.8"}],
        }
        out = versions.merge(child, parent)
        self.assertEqual(out["id"], "fabric")
        self.assertEqual(out["jar"], "1.21.1")
        self.assertEqual(out["mainClass"], "fabric.Main")
        self.assertEqual(out["arguments"]["jvm"], ["-Dp", "-Dc"])
        self.assertEqual([l["name"] for l in out["libraries"]],
                         ["org.ow2.asm:asm:9.8", "org.lwjgl:lwjgl:3.3.3",
                          "org.lwjgl:lwjgl:3.3.3:natives-linux"])
        self.assertNotIn("inheritsFrom", out)


class LaunchTest(unittest.TestCase):
    SESSION = {"name": "Steve", "uuid": "abc", "token": "SECRET", "type": "msa"}

    def test_modern_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = Paths(tmp)
            version = {
                "id": "1.21.1", "jar": "1.21.1", "mainClass": "Main", "type": "release",
                "assetIndex": {"id": "17"},
                "libraries": [{"name": "a:b:1", "downloads": {"artifact": {
                    "path": "a/b/1/b-1.jar", "url": "https://x/b-1.jar", "sha1": "0"}}}],
                "arguments": {
                    "jvm": ["-cp", "${classpath}"],
                    "game": ["--username", "${auth_player_name}",
                             "--accessToken", "${auth_access_token}",
                             {"rules": [{"action": "allow",
                                         "features": {"has_custom_resolution": True}}],
                              "value": ["--width", "${resolution_width}"]},
                             {"rules": [{"action": "allow",
                                         "features": {"is_demo_user": True}}],
                              "value": "--demo"}],
                },
            }
            cmd = launch.build_command(paths, version, self.SESSION, "java",
                                       memory_mb=4096, resolution=(800, 600))
            self.assertEqual(cmd[:2], ["java", "-Xmx4096M"])
            cp = cmd[cmd.index("-cp") + 1]
            self.assertIn(str(Path(tmp) / "libraries/a/b/1/b-1.jar"), cp)
            self.assertTrue(cp.endswith(str(paths.version_jar("1.21.1"))))
            self.assertEqual(cmd[cmd.index("--username") + 1], "Steve")
            self.assertEqual(cmd[cmd.index("--width") + 1], "800")
            self.assertNotIn("--demo", cmd)
            self.assertLess(cmd.index("Main"), cmd.index("--username"))
            self.assertNotIn("SECRET", launch.redact(cmd))

    def test_legacy_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            version = {"id": "1.8.9", "jar": "1.8.9", "mainClass": "Main",
                       "libraries": [], "assetIndex": {"id": "1.8"},
                       "minecraftArguments": "--username ${auth_player_name} --assetIndex ${assets_index_name}"}
            cmd = launch.build_command(Paths(tmp), version, self.SESSION, "java")
            self.assertIn("-cp", cmd)
            self.assertTrue(any(a.startswith("-Djava.library.path=") for a in cmd))
            self.assertEqual(cmd[-4:], ["--username", "Steve", "--assetIndex", "1.8"])


class AuthTest(unittest.TestCase):
    def test_session_requires_login_even_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(auth.AuthError):
                auth.session(Paths(tmp), offline=True)

    def test_store_and_logout(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = Paths(tmp)
            auth._store(paths, {"refresh_token": "r"},
                        {"access_token": "t", "expires_in": 3600},
                        {"name": "Steve", "id": "u1"})
            self.assertEqual(auth.session(paths)["token"], "t")
            self.assertEqual(auth.session(paths, offline=True)["token"], "0")
            self.assertEqual(paths.accounts.stat().st_mode & 0o077, 0)
            self.assertTrue(auth.logout(paths))
            self.assertIsNone(auth.active_account(paths))
            self.assertFalse(auth.logout(paths))


if __name__ == "__main__":
    unittest.main()
