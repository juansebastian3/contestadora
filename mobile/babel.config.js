module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [], // Deja esto vacío por ahora para descartar el error
  };
};