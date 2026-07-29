/*
 * icy_gst.c
 *
 * Play an Icecast / Shoutcast stream with GStreamer and print StreamTitle updates.
 *
 * Build:
 *   gcc `pkg-config --cflags --libs gstreamer-1.0 gio-2.0 glib-2.0` -o radio-icy radio-icy.c
 *
 * Usage:
 *   ./icy_gst "http://your.icecast.server:8000/mount"
 *
 * Notes:
 * - playbin handles many transport details; the stream's ICY metadata will typically
 *   appear as GST_MESSAGE_TAG messages on the bus.
 * - This program prints title and artist when tags arrive.
 */

#include <gst/gst.h>
#include <glib.h>

static gboolean
bus_call (GstBus *bus, GstMessage *msg, gpointer user_data)
{
    GMainLoop *loop = (GMainLoop *) user_data;

    switch (GST_MESSAGE_TYPE (msg)) {
    case GST_MESSAGE_EOS:
        g_print ("End-Of-Stream\n");
        g_main_loop_quit (loop);
        break;

    case GST_MESSAGE_ERROR: {
        GError *err = NULL;
        gchar *dbg = NULL;
        gst_message_parse_error (msg, &err, &dbg);
        g_printerr ("ERROR: %s\n", err->message);
        if (dbg) g_printerr ("Debug info: %s\n", dbg);
        g_error_free (err);
        g_free (dbg);
        g_main_loop_quit (loop);
        break;
    }

    case GST_MESSAGE_STATE_CHANGED: {
        /* Optionally handle state changes if you want */
        break;
    }

    case GST_MESSAGE_TAG: {
        GstTagList *tags = NULL;
        gchar *title = NULL;
        gchar *artist = NULL;
        gchar *val = NULL;

        gst_message_parse_tag (msg, &tags);

        /* Try standard tags first */
        if (gst_tag_list_get_string (tags, GST_TAG_TITLE, &title)) {
            /* title available */
        } else if (gst_tag_list_get_string (tags, "icy-title", &title)) {
            /* Some sources might use a custom tag name */
        } else if (gst_tag_list_get_string (tags, "StreamTitle", &title)) {
            /* fallback to raw stream tag name */
        }

        if (gst_tag_list_get_string (tags, GST_TAG_ARTIST, &artist)) {
            /* artist available */
        } else if (gst_tag_list_get_string (tags, "icy-name", &artist)) {
            /* station name sometimes appears here */
        }

        /* Print out any discovered metadata nicely */
        if (title || artist) {
            g_print ("---- METADATA UPDATE ----\n");
            if (title) {
                g_print ("Title : %s\n", title);
                g_free (title);
            }
            if (artist) {
                g_print ("Artist: %s\n", artist);
                g_free (artist);
            }
        } else {
            /* If nothing recognized, print the whole tag list (for debugging) */
            gchar *debug = gst_tag_list_to_string (tags);
            g_print ("Tags: %s\n", debug);
            g_free (debug);
        }

        if (tags)
            gst_tag_list_free (tags);

        break;
    }

    default:
        break;
    }

    return TRUE;
}

int main (int argc, char *argv[])
{
    GMainLoop *loop;
    GstElement *pipeline;
    GstBus *bus;
    GstStateChangeReturn ret;

    gst_init (&argc, &argv);

    if (argc != 2) {
        g_printerr ("Usage: %s <stream-uri>\n", argv[0]);
        g_printerr ("Example: %s http://icecast.example.org:8000/mount\n", argv[0]);
        return -1;
    }

    const gchar *uri = argv[1];

    loop = g_main_loop_new (NULL, FALSE);

    /* Create playbin (high-level player). It will pick appropriate src (souphttpsrc / shout2src)
     * and decoders for the stream. */
    pipeline = gst_element_factory_make ("playbin", "player");
    if (!pipeline) {
        g_printerr ("Failed to create playbin element. Is GStreamer installed?\n");
        return -1;
    }

    g_object_set (G_OBJECT (pipeline), "uri", uri, NULL);

    /* Optionally tell playbin to request ICY metadata.
     * Many sources provide it automatically; but to be explicit, you can set:
     *   g_object_set(pipeline, "flags", GST_PLAY_FLAG_TEXT, NULL);
     * However in practice playbin listens for tags by default. */

    /* Watch the bus for messages */
    bus = gst_element_get_bus (pipeline);
    gst_bus_add_watch (bus, bus_call, loop);
    gst_object_unref (bus);

    /* Start playing */
    ret = gst_element_set_state (pipeline, GST_STATE_PLAYING);
    if (ret == GST_STATE_CHANGE_FAILURE) {
        g_printerr ("Failed to set pipeline to PLAYING\n");
        gst_object_unref (pipeline);
        return -1;
    }

    g_print ("Playing: %s\n", uri);
    g_print ("Press Ctrl+C to stop.\n");

    /* Run mainloop; tags will be printed from bus callback */
    g_main_loop_run (loop);

    /* Clean up */
    gst_element_set_state (pipeline, GST_STATE_NULL);
    gst_object_unref (pipeline);
    g_main_loop_unref (loop);

    return 0;
}
