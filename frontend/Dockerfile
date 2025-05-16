# Utilizar una imagen base de Node.js
FROM node:18

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto de la aplicación
COPY . .

# Construir la aplicación de React
RUN npm run build

# Exponer el puerto del servidor de desarrollo
EXPOSE 3000

# Comando para ejecutar la aplicación
CMD ["npm", "start"]
