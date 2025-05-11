import click


class AliasedCommandGroup(click.Group):
    """Work in progress."""

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if exact := super().get_command(ctx, cmd_name):
            return exact

        candidates = self.list_commands(ctx)

        for matcher in self._startswith, self._dashes:
            matches = matcher(candidates, cmd_name)
            if len(matches) == 1:
                match = matches[0]
                # print(f"{type(self).__name__}: Subcommand {match!r} selected by matcher={matcher.__name__}().")
                return super().get_command(ctx, match)

        # ctx.fail(f"Ambiguous alias `{cmd_name}`: {', '.join(sorted(matches))}")  # Multiple matches
        return None

    @classmethod
    def _startswith(cls, candidates: list[str], cmd_name: str) -> list[str]:
        return [c for c in candidates if c.startswith(cmd_name)]

    @classmethod
    def _dashes(cls, candidates: list[str], cmd_name: str) -> list[str]:
        return [c for c in candidates if "".join(part[0] for part in c.split("-")) == cmd_name]

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        _, cmd, args = super().resolve_command(ctx, args)

        if cmd is None:
            return None, None, args

        return cmd.name, cmd, args
