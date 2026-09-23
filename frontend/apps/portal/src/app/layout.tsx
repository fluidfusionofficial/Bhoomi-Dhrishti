import type { Metadata } from 'next';
import { Public_Sans, IBM_Plex_Serif } from 'next/font/google';
import './globals.css';

const publicSans = Public_Sans({
  subsets: ['latin'],
  variable: '--font-public-sans',
  display: 'swap',
});

const ibmPlexSerif = IBM_Plex_Serif({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-ibm-plex-serif',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Bhoomi Dhrishti — Select Your Role',
  description:
    'Integrated GIS-based Digital Public Infrastructure for Land Governance. Department of Land Resources (DoLR), Ministry of Rural Development.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${publicSans.variable} ${ibmPlexSerif.variable}`}>
      <body className="font-sans antialiased bg-[#F4F7FB] text-[#16212E]">
        {children}
      </body>
    </html>
  );
}
