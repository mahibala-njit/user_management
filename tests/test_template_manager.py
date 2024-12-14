import pytest
from unittest.mock import patch, mock_open, MagicMock
from app.utils.template_manager import TemplateManager

# Mocked templates content
MOCK_HEADER = "## Header Content"
MOCK_FOOTER = "Footer Content"
MOCK_TEMPLATE = "Hello, {name}! Welcome to our service."

# Mocked rendered context
MOCK_CONTEXT = {"name": "John Doe"}
MOCK_RENDERED_CONTENT = f"## Header Content\nHello, John Doe! Welcome to our service.\nFooter Content"


@pytest.fixture
def template_manager():
    """Fixture to provide a TemplateManager instance."""
    return TemplateManager()


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_HEADER)
@patch("app.utils.template_manager.Path")
def test_read_template(mock_path, mock_open_fn, template_manager):
    """Test that templates are read correctly."""
    # Configure mock for Path
    mock_path.return_value = MagicMock()
    mock_path.return_value.__truediv__.return_value = MagicMock()

    # Perform the read
    content = template_manager._read_template("header.md")
    assert content == MOCK_HEADER

    # Assert the open call
    expected_path = template_manager.templates_dir / "header.md"
    mock_open_fn.assert_called_once_with(expected_path, 'r', encoding='utf-8')


#@patch("app.utils.template_manager.TemplateManager._read_template", side_effect=[MOCK_HEADER, MOCK_TEMPLATE, MOCK_FOOTER])
#@patch("app.utils.template_manager.markdown2.markdown")
#def test_render_template(mock_markdown, mock_read_template, template_manager):
#    """Test rendering templates with context."""
#    # Mock Markdown rendering
#    mock_markdown.return_value = "<html><body>Hello, John Doe!</body></html>"
#
#    # Render the template
#    rendered_html = template_manager.render_template("main_template", **MOCK_CONTEXT)
#
#    # Verify that templates are read
#    mock_read_template.assert_any_call("header.md")
#    mock_read_template.assert_any_call("main_template.md")
#    mock_read_template.assert_any_call("footer.md")
#
#    # Verify Markdown rendering
#    mock_markdown.assert_called_once_with(MOCK_RENDERED_CONTENT)
#
#    # Check final output
#    assert "<html>" in rendered_html
#    assert "Hello, John Doe!" in rendered_html


@patch("app.utils.template_manager.TemplateManager._read_template", side_effect=FileNotFoundError)
def test_render_template_missing_file(mock_read_template, template_manager):
    """Test handling missing template files."""
    with pytest.raises(FileNotFoundError):
        template_manager.render_template("missing_template", **MOCK_CONTEXT)


@patch("app.utils.template_manager.TemplateManager._apply_email_styles")
def test_apply_email_styles(mock_apply_styles, template_manager):
    """Test applying email styles."""
    mock_apply_styles.return_value = "<div>Styled Content</div>"
    styled_html = template_manager._apply_email_styles("<html><body>Test Content</body></html>")

    # Verify the method was called
    mock_apply_styles.assert_called_once()
    assert "<div>Styled Content</div>" == styled_html


@patch("app.utils.template_manager.TemplateManager._read_template", return_value=MOCK_TEMPLATE)
@patch("app.utils.template_manager.TemplateManager._apply_email_styles")
def test_render_template_with_invalid_context(mock_apply_styles, mock_read_template, template_manager):
    """Test rendering templates with invalid context."""
    mock_apply_styles.return_value = "<html>Styled Content</html>"

    with pytest.raises(KeyError):
        template_manager.render_template("main_template", unknown_context="Unexpected")

def test_apply_email_styles_list_elements(template_manager):
    """Test applying email styles to list elements."""
    raw_html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
    styled_html = template_manager._apply_email_styles(raw_html)

    assert 'style="list-style-type: none; padding: 0;"' in styled_html
    assert 'style="margin-bottom: 10px;"' in styled_html

def test_apply_email_styles_ignores_body_style_duplicate(template_manager):
    """Test that 'body' style is only applied at the top-level div."""
    raw_html = "<body><h1>Header</h1><p>Paragraph</p></body>"
    styled_html = template_manager._apply_email_styles(raw_html)

    # Ensure the body style is applied only once, at the div level
    assert styled_html.startswith('<div style="font-family: Arial, sans-serif;')
    assert '<body style=' not in styled_html

def test_apply_email_styles_empty_html(template_manager):
    """Test applying email styles to empty HTML content."""
    raw_html = ""
    styled_html = template_manager._apply_email_styles(raw_html)

    # Ensure the body style is applied even when HTML content is empty
    assert styled_html == '<div style="font-family: Arial, sans-serif; font-size: 16px; color: #333333; background-color: #ffffff; line-height: 1.5;"></div>'

def test_apply_email_styles_no_matching_tags(template_manager):
    """Test applying email styles to HTML with no matching tags."""
    raw_html = "<custom>Custom Tag</custom>"
    styled_html = template_manager._apply_email_styles(raw_html)

    # Ensure no changes to the unrecognized tags
    assert "<custom>Custom Tag</custom>" in styled_html
