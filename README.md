# distcomp-services

Procedures and change records for the distributed computing services hosted at BNL for ePIC: the PanDA server and JEDI, harvester, iDDS and the CRIC configuration. Each service has a directory holding its standing procedures and its change log. Directories for harvester, iDDS and CRIC are added with their first documents.

| Service | Host | Documents |
|---|---|---|
| PanDA server and JEDI | `pandaserver01.sdcc.bnl.gov` | [panda-server/UPGRADE.md](panda-server/UPGRADE.md), [panda-server/CHANGES.md](panda-server/CHANGES.md) |
| harvester | `pandaharvester01.sdcc.bnl.gov` | |

## Conventions

- A procedure document is standing and revised in place.
- A pending change is planned in the service's procedure document and circulated to PanDA operations at BNL and the maintainers of the software for comment before execution.
- Every change to a service is logged in the service's `CHANGES.md`, newest first: the date, the role that made the change, what changed (package versions with commits, configuration files with the motivation), how it was verified, and the rollback copy. The log is the shared view of the service's state.
- Plain Markdown, no build. Changes by direct commit or pull request.

Maintained by PanDA operations at BNL and the operators of the ePIC production system.
