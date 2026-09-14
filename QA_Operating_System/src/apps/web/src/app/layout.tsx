import './globals.css'

export const metadata = {
  title: 'AI QA Operating System',
  description: 'Command Center for the AI QA Operating System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="flex bg-white text-black">
        <aside className="w-64 border-r-2 border-black h-screen p-6 flex flex-col gap-8 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-black"></div>
            <h1 className="font-black text-2xl uppercase tracking-tighter">QA OS</h1>
          </div>
          <nav className="flex flex-col gap-3 font-bold uppercase tracking-widest text-xs">
            <a href="/" className="px-4 py-3 bg-black text-white border-2 border-black">Command Center</a>
            <a href="/reviews" className="px-4 py-3 bg-white text-black border-2 border-black hover:bg-gray-100 transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-y-[2px] hover:translate-x-[2px]">Human Reviews</a>
            <a href="/graph" className="px-4 py-3 bg-white text-black border-2 border-black hover:bg-gray-100 transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-y-[2px] hover:translate-x-[2px]">Graph Explorer</a>
          </nav>
        </aside>
        <main className="flex-1 overflow-y-auto p-10 h-screen bg-white">
          {children}
        </main>
      </body>
    </html>
  )
}
