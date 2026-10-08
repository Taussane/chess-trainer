# Accounts and game sites: the plan

Decided before building accounts, so adding Chess.com (or another site) later only adds to it and never reorganises what exists.

## Accounts

- **An account is ours, not a site's.** Each player has an internal account id. Sites are *connections* attached to it, so one account can have several, and signing in with any verified connection opens the same account.
- **Connections** (one row each): `site` (`lichess`, later `chesscom`), the player's id and username on that site, and whether it is verified (signed in through that site) or only typed (a username, enough to read public games).
- **Now:** sign-in with Lichess or with Google (both verified; Google is for players without Lichess, until Chess.com approves our sign-in). Google's ID token is checked by the server (signature, our client id, expiry, verified email), which then gives the page a login of its own (`X-Auth-Site: app`, valid until logging out or 180 days unused). A Chess.com username can be added (unverified, checked to exist), kept in the account's `meta/chesscom` document; the server reads that player's public games from Chess.com (`/api/chesscom/games`), so they come in like Lichess games. Typed usernames are not unique between accounts: they only read public games. If Chess.com approves our sign-in, it becomes a second verified way into the same account; a player with only Chess.com can then create an account with it.
- **Linking:** logged in one way, "Also log in with …" in the profile adds the other login to the account (`/api/link/google`, `/api/link/lichess`). If that login already had its own account, it is merged in: results and games added (on a clash, the account you're in keeps its own), settings filled in where missing, its logins moved over, then it is deleted.
- **Two accounts, one person:** if someone signs in with Chess.com and it is already connected to another account, they are offered to merge; never a silent second account.

## Stored per account

| What | Key | Notes |
| --- | --- | --- |
| Results | account, time, exercise | Each row also keeps the position key, where the position came from (`masters` or a site), and whether it was a miss. Missed positions are read from these rows. |
| Games | account, site, the site's game id | Moves, evaluations (the site's or the app's), the app's engine checks. Each game says which site it came from. |
| Profile | account | Joined date, preferences (bullet games, …), the daily routine's resume point. |

Positions found in a player's games are not stored: they are worked out again from the games, so a rule change applies to old games too.

## Ids that stay stable

- **Lichess games** keep their Lichess id as is (8 characters), as today: nothing saved now has to change.
- **Games from any other site** get a prefix: `cc-` and the Chess.com game number for Chess.com; games added as a file with no site id keep today's `g…` code made from their moves.
- **Position keys** stay `own:<game id>:<half-move>`, so they are unique across sites through the game id.

## Downloading games

One function per site returns PGN text; everything after it (reading the games, finding positions, the background analysis) is shared and does not care where the games came from.

- **Lichess:** the game export (`/api/games/user/<name>`), with Lichess's own evaluations where the game was analysed.
- **Chess.com:** the public game API (`api.chess.com/pub/player/<name>/games/<year>/<month>/pgn`), month by month until there are enough games, one request at a time as Chess.com asks. No evaluations: every game gets the app's quick scan.

## Server

A small Cloudflare Worker with a D1 database. It checks each request's sign-in with the site that issued it (for Lichess: `/api/account` with the player's token), then reads or writes only that account's rows. The browser keeps a copy of everything, so the app opens instantly and works offline, and sends what was played offline when it reconnects.
