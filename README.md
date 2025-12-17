# Google Sans Code - Plus Plus

Added more devicons from nerd fonts.

## Installation

Checkout the release, or you may wanna build it on your own.

## Build

Build the inital GoogleSansCode to ./nerdfont-patcher/

```bash
cd ./nerdfont-patcher/Google_Sans_Code/static

docker run --rm \
  -v "$(pwd)/GoogleSansCode-Medium.ttf":/in/GoogleSansCode-Medium.ttf:Z \
  -v "$(pwd)/output":/out:Z \
  nerdfonts/patcher --complete
```

You may replace the "Medium" with "Bold" or whatever and build more kinds.

You may add more flags. Check Nerd Font Pather for more.

## TODO

- Anyone knows if it's possible to hard-code these icons into the source code?

## License

This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at [https://openfontlicense.org](https://openfontlicense.org)

See [AUTHORS.txt](/AUTHORS.txt) for a list of copyright authors, including organizations like Google LLC.
See [CONTRIBUTORS.txt](/CONTRIBUTORS.txt) for a list of individual people who have contributed.

Also see [TRADEMARKS.md](/TRADEMARKS.md) regarding naming issues.
