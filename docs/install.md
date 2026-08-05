# Installing and enabling

The two install routes are in the [README](../README.md#install). This is the
detail behind them: setting the plugin by hand, and what enabling it everywhere
actually costs.

## Enabling by hand

Installing writes the plugin into `enabledPlugins`. You can also set it yourself,
in `~/.claude/settings.json` for every project or a project's
`.claude/settings.json` for one:

```json
{
  "enabledPlugins": {
    "observe@durchnull": true
  }
}
```

## Enabling it everywhere is safe

Until a project activates a capability in its `.claude/observe/config.json`, both
hooks exit silently and nothing is written — so a globally enabled `observe` costs
a project that never configured it nothing at all.

The hook commands also guard on `command -v python3`, so a machine without Python
degrades to a silent no-op instead of printing a hook error on every turn.
