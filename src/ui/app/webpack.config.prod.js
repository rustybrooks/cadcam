const webpack = require('webpack');
// const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const merge = require('webpack-merge');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
const baseConfig = require('./webpack.config.base.js');
const path = require('path')

module.exports = merge(baseConfig, {
  mode: 'production',

  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          {
            loader: 'style-loader' ,
          },
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
            },
          },
        ],
      },
    ]
  },

  plugins: [
    // Minify JS
    new UglifyJsPlugin({
      sourceMap: false,
      // compress: true,
    }),
    // Minify CSS
    new webpack.LoaderOptionsPlugin({
      minimize: true,
    }),
  ],

  output: {
    path: path.resolve('dist'),
    filename: 'main.js',
  },
});
