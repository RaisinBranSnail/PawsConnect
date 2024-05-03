const path = require('path');

module.exports = {
  // Ensures dependencies are transpiled correctly
  transpileDependencies: true,

  // DevServer configuration to handle API requests in development
  devServer: {
    proxy: {
      '/api': {
        target: 'https://localhost:8080',
        ws: true,
        changeOrigin: true,
        pathRewrite: { '^/api': '' },
      }
    }
  },

  // Webpack configuration to define the '@' alias
  configureWebpack: {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src/'),  // Sets '@' to reference the 'src' directory
      }
    }
  }
};