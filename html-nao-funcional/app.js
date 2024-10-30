new Vue({
  el: '#app',
  data: {
    fileInfo: ''
  },
  methods: {
    onFileChange(event) {
      const file = event.target.files[0];
      if (file) {
        this.fileInfo = `Arquivo selecionado: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
      } else {
        this.fileInfo = 'Nenhum arquivo selecionado';
      }
    },
    handleFileUpload() {
      alert('Arquivo enviado com sucesso!');
      this.fileInfo = '';
      document.getElementById('arquivo').value = '';
    }
  }
});
