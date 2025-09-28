import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";

import "./globals.css";


const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Student Manager",
  description: "基于 Next.js 与 FastAPI 的学生管理系统模板",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {


  return (
    <html lang="zh">
      <body
        className={`${geistSans.variable} ${geistMono.variable} flex min-h-screen flex-col antialiased`}
      >
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
      </body>
    </html>
  );
}
