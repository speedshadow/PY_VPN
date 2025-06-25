from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    spam_check = forms.IntegerField(
        label="Anti-Spam Question: What is 5 + 5?",
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'placeholder': 'Your answer'
        })
    )

    class Meta:
        model = Comment
        fields = ('author_name', 'author_email', 'content')
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'John Doe'
            }),
            'author_email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'you@example.com'
            }),
            'content': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'rows': 4,
                'placeholder': 'Leave your comment here...'
            }),
        }
        labels = {
            'author_name': 'Your Name',
            'author_email': 'Your Email',
            'content': 'Comment',
        }

    def clean_spam_check(self):
        answer = self.cleaned_data.get('spam_check')
        if answer != 10:
            raise forms.ValidationError("Your answer to the anti-spam question is incorrect.")
        return answer
from .models import BlogPost

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        base_input_classes = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-pink-500 focus:ring-pink-500 sm:text-sm'
        checkbox_classes = 'h-4 w-4 text-pink-600 border-gray-300 rounded focus:ring-pink-500 align-middle'
        file_input_classes = (
            'mt-1 block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 '
            'focus:outline-none focus:ring-pink-500 focus:border-pink-500 '
            'file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold '
            'file:bg-pink-100 file:text-pink-700 hover:file:bg-pink-200'
        )

        self.fields['title'].widget.attrs.update({'class': base_input_classes, 'placeholder': 'Enter blog post title'})
        self.fields['slug'].widget.attrs.update({'class': base_input_classes + ' bg-gray-100', 
                                                 'placeholder': 'e.g., my-awesome-post (auto-generated if blank)'})
        self.fields['author'].widget.attrs.update({'class': base_input_classes, 'placeholder': 'Author name'})
        
        self.fields['published'].widget.attrs.update({'class': checkbox_classes})
        
        if 'published_date' in self.fields:
            self.fields['published_date'].widget = forms.DateTimeInput(
                attrs={'class': base_input_classes, 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            )
            self.fields['published_date'].required = False
            self.fields['published_date'].help_text = 'Optional. If "Published" is checked and this is blank, current time might be used (depending on view/model logic).'

        if 'featured_image' in self.fields:
            self.fields['featured_image'].widget.attrs.update({'class': file_input_classes})
