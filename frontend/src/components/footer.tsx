export function Footer() {
  return (
    <footer className="bg-space-gray border-t border-gray-700 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* About */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-stellar-blue">
              About This Project
            </h3>
            <p className="text-gray-400 text-sm">
              Built for the 2025 NASA Space Apps Challenge to democratize access 
              to space biology research and accelerate scientific discovery.
            </p>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-galaxy-teal">
              Resources
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="https://osdr.nasa.gov" className="text-gray-400 hover:text-white transition-colors">
                  NASA OSDR
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  API Documentation
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  User Guide
                </a>
              </li>
            </ul>
          </div>

          {/* Technology */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-nebula-pink">
              Technology
            </h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>Next.js & React</li>
              <li>Local Transformer Models</li>
              <li>Neo4j Knowledge Graph</li>
              <li>D3.js Visualizations</li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-cosmic-purple">
              Contact
            </h3>
            <p className="text-gray-400 text-sm mb-2">
              Built with ❤️ for space exploration
            </p>
            <div className="text-sm text-gray-500">
              2025 NASA Space Apps Challenge
            </div>
          </div>
        </div>

        <div className="border-t border-gray-700 mt-8 pt-6 flex flex-col md:flex-row justify-between items-center">
          <div className="text-gray-400 text-sm">
            © 2025 NASA Space Biology Knowledge Engine. MIT License.
          </div>
          <div className="text-gray-400 text-sm mt-2 md:mt-0">
            Powered by NASA Open Science Data Repository
          </div>
        </div>
      </div>
    </footer>
  )
}