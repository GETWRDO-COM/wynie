import cn from "classnames";
import "@/styles/app.sass";
import type { Metadata } from "next";
import { Rubik } from "next/font/google";
import localFont from "next/font/local";
import { Providers } from "./providers";

const hostGrotesk = localFont({ src: "./fonts/HostGrotesk-Bold.woff2" });

const rubik = Rubik({
    weight: ["300", "400", "500", "600", "700"],
    subsets: ["latin"],
    display: "block",
    variable: "--font-rubik",
});

export const metadata: Metadata = {
    title: "Bento Cards: Landing",
    description: "Minimal to-do list app UI design kit + landing page",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <head>
                {/* Description no longer than 155 characters */}
                <meta name="description" content="Bento Cards: SimpleList" />
                {/* Product Name */}
                <meta name="product-name" content="Bento Cards: SimpleList" />
                {/* Twitter Card data */}
                <meta name="twitter:card" content="summary" />
                <meta name="twitter:site" content="@ui8" />
                <meta name="twitter:title" content="Bento Cards: SimpleList" />
                <meta
                    name="twitter:description"
                    content="Minimal to-do list app UI design kit + landing page"
                />
                <meta name="twitter:creator" content="@ui8" />
                {/* Twitter Summary card images must be at least 120x120px */}
                <meta
                    name="twitter:image"
                    content="%PUBLIC_URL%/twitter-card.png"
                />

                {/* Open Graph data for Facebook */}
                <meta property="og:title" content="Bento Cards: SimpleList" />
                <meta property="og:type" content="Article" />
                <meta
                    property="og:url"
                    content="https://ui8.net/ui8/products/bento-cards-simplelist"
                />
                <meta
                    property="og:image"
                    content="%PUBLIC_URL%/fb-og-image.png"
                />
                <meta
                    property="og:description"
                    content="Minimal to-do list app UI design kit + landing page"
                />
                <meta
                    property="og:site_name"
                    content="Bento Cards: SimpleList"
                />
                <meta property="fb:admins" content="132951670226590" />

                {/* Open Graph data for LinkedIn */}
                <meta property="og:title" content="Bento Cards: SimpleList" />
                <meta
                    property="og:url"
                    content="https://ui8.net/ui8/products/bento-cards-simplelist"
                />
                <meta
                    property="og:image"
                    content="%PUBLIC_URL%/linkedin-og-image.png"
                />
                <meta
                    property="og:description"
                    content="Minimal to-do list app UI design kit + landing page"
                />

                {/* Open Graph data for Pinterest */}
                <meta property="og:title" content="Bento Cards: SimpleList" />
                <meta
                    property="og:url"
                    content="https://ui8.net/ui8/products/bento-cards-simplelist"
                />
                <meta
                    property="og:image"
                    content="%PUBLIC_URL%/pinterest-og-image.png"
                />
                <meta
                    property="og:description"
                    content="Minimal to-do list app UI design kit + landing page"
                />
            </head>
            <body className={cn(rubik.className, hostGrotesk.className)}>
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
