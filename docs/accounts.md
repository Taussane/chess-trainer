# Accounts and game sites

How players' accounts and their game sites work. Adding another site only adds to this; nothing existing is reorganised.

## Accounts

- **An account is ours, not a site's.** Each player has an internal account id. Sites are *connections* attached to it, so one account can have several, and signing in with any verified connection opens the same account.
- **Connections** (one row each): `site` (`lichess`, `google`; a Chess.com username is kept in `meta/chesscom` instead), the player's id and username on that site, and whether it is verified (signed in through that site) or only typed (a username, enough to read public games).
- **Now:** sign-in with Lichess or with Google (both verified; Google is for players without Lichess, until Chess.com approves our sign-in). Google's ID token is checked by the server (signature, our client id, expiry, verified email), which then gives the page a login of its own (`X-Auth-Site: app`, valid until logging out or 180 days unused). A Chess.com username can be added (unverified, checked to exist), kept in the account's `meta/chesscom` document; the server reads that player's public games from Chess.com (`/api/chesscom/games`), so they come in like Lichess games. Typed usernames are not unique between accounts: they only read public games. If Chess.com approves our sign-in, it becomes a second verified way into the same account; a player with only Chess.com can then create an account with it.
- **Linking:** Lichess is the main login. An account opened with Google can "Connect Lichess" (profile); from then on it shows as a Lichess account (the Google login still opens it, but is not shown, and Lichess cannot be removed) (`/api/link/lichess`; the server also has `/api/link/google` and `DELETE /api/link/lichess`, not offered in the app). If that login already had its own account, it is merged in: results and games added (on a clash, the account you're in keeps its own), settings filled in where missing ("training since": the earlier date), its logins moved over, then it is deleted.
- **If Chess.com sign-in comes — two accounts, one person:** if someone signs in with Chess.com and it is already connected to another account, they are offered to merge; never a silent second account.

## Stored per account

| What | Key | Notes |
| --- | --- | --- |
| Results | account, time, exercise | Each row also keeps the position key, where the position came from (`masters` or a site), and whether it was a miss. Missed positions are read from these rows. |
| Games | account, site, the site's game id | Moves, evaluations (the site's or the app's), the app's engine checks. Each game says which site it came from. |
| Settings | account, name | `profile` (joined date), `chesscom` (the username), `games-cleared` (inside Claude's "Remove my games"), `replay` (older saves' missed positions). |

Positions found in a player's games are not stored in the account: each device works them out from the games and keeps them in the browser with a signature of the rules and of the game, so a rule change or new analysis finds them again (a few games at a time, so the page never freezes).

## Ids that stay stable

- **Lichess games** keep their Lichess id as is (8 characters).
- **Games from any other site** get a prefix: `cc-` and the Chess.com game number for Chess.com; games added as a file with no site id get a `g…` code made from their moves.
- **Position keys** stay `own:<game id>:<half-move>`, so they are unique across sites through the game id.

## Downloading games

One function per site returns PGN text; everything after it (reading the games, finding positions, the background analysis) is shared and does not care where the games came from.

- **Lichess:** the game export (`/api/games/user/<name>`), with Lichess's own evaluations where the game was analysed.
- **Chess.com:** the public game API (`api.chess.com/pub/player/<name>/games/<year>/<month>/pgn`), month by month until there are enough games, one request at a time as Chess.com asks. No evaluations: every game gets the app's quick scan.
- **How many:** each site's last 100 games (bullet to classical; UltraBullet, daily games and variants left out) form the core list; an older game stays only while it has missed positions to replay (at most 100 such games per site). Ratings, time control and date are kept with each game.
- **Removing games:** disconnecting Chess.com removes its games and their positions; an account with Lichess keeps it (its games go with the account). The website has no "Remove my games"; inside Claude, where games are added as files, it remains.

## Server

A small Cloudflare Worker with a D1 database. It checks each request's sign-in (Lichess: `/api/account` with the player's token, remembered for a day; Google: the server's own token, given at login after checking Google's ID token), then reads or writes only that account's rows. The browser keeps a copy of everything, so the app opens instantly and works offline, and sends what was played offline when it reconnects.
