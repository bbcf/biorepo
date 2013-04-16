import tw2.forms as twf
from tw2.forms.fields import TableForm


#FORM
class NewUCSCForm(TableForm):
    position = twf.Textfield(label_text="Position", help_text="Example = chr17:36,615,540-36,621,822")
    gene = twf.Textfield(label_text="Gene", help_text="fill the blank with the gene name of your choice")
