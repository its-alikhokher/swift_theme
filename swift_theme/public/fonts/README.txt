Optional: serve Inter from this app instead of the Google Fonts CDN.

1. Download Inter.var.woff2 from https://github.com/rsms/inter/releases
2. Rename it to inter-var.woff2 and put it in this folder
3. In public/css/swift-fonts.css, add it back as the first src of the Inter
   @font-face:

     src: url("/assets/swift_theme/fonts/inter-var.woff2") format("woff2-variations"),
          url("https://fonts.gstatic.com/...") format("woff2");

Step 3 matters: the url is not there by default because naming a file that
does not ship made every page load fetch it and get a 404 before falling
through to the CDN.
