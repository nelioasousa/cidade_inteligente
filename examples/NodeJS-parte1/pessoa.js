function Pessoa(nome, cidade, telefone, ano) {
  this.nome = nome;
  this.cidade = cidade;
  this.telefone = telefone;
  this.ano = ano;
}

Pessoa.prototype.toString = function() {
  return this.nome+', '+this.cidade+', '+this.telefone+', '+this.ano;

}

module.exports = Pessoa;







