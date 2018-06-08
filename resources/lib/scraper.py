# -*- coding: utf-8 -*-
import os
import re
import xbmc
import xbmcgui
import xbmcaddon

# Import the common settings
from settings import Settings
from settings import log
from settings import os_path_join
from settings import os_path_split
from settings import list_dir
from settings import normalize_string
from settings import dir_exists
from themeFetcher import TvTunesFetcher

ADDON = xbmcaddon.Addon(id='script.tvtunes')


#################################
# Core TvTunes Scraper class
#################################
class TvTunesScraper():
    def __init__(self):
        # Get the name of the theme we are looking for
        videoItem = self.getSoloVideo()

        # Check if multiple themes are suported
        if not Settings.isMultiThemesSupported():
            # Check if a theme already exists
            if self._doesThemeExist(videoItem['path']):
                # Prompt the user to see if we should overwrite the theme
                if not xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32103), ADDON.getLocalizedString(32104)):
                    # No not want to overwrite, so quit
                    log("TvTunesScraper: %s already exists" % (os_path_join(videoItem['path'], "theme.*")))
                    return

        # Perform the fetch
        videoList = []
        videoList.append(videoItem)
        TvTunesFetcher(videoList)

    # Handles the case where there is just a single theme to look for
    # and it has been invoked from the given video location
    def getSoloVideo(self):
        log("getSoloVideo: solo mode")

        # Used to pass the name and path via the command line
        # This caused problems with non ascii characters, so now
        # we just look at the screen details
        # The solo option is only available from the info screen
        # Looking at the TV Show information page
        isTvShow = self._isTv()
        if isTvShow:
            videoName = xbmc.getInfoLabel("ListItem.TVShowTitle")
            log("getSoloVideo: TV Show detected %s" % videoName)
        else:
            videoName = xbmc.getInfoLabel("ListItem.Title")
            log("getSoloVideo: Movie detected %s" % videoName)

        # Now get the video path
        videoPath = None
        if xbmc.getCondVisibility("Window.IsVisible(movieinformation)") and isTvShow:
            videoPath = xbmc.getInfoLabel("ListItem.FilenameAndPath")
        if videoPath is None or videoPath == "":
            videoPath = xbmc.getInfoLabel("ListItem.Path")
        log("getSoloVideo: Video Path %s" % videoPath)

        # Check if there is an "Original Title Defines
        originalTitle = xbmc.getInfoLabel("ListItem.OriginalTitle")
        if (originalTitle is not None) and (originalTitle != ""):
            originalTitle = normalize_string(originalTitle)
        else:
            originalTitle = None

        normVideoName = normalize_string(videoName)
        log("getSoloVideo: videoName = %s" % normVideoName)

        # If the main title and the original title are the same
        # Then no need to use the original title
        if (originalTitle == normVideoName):
            originalTitle = None

        if Settings.isCustomPathEnabled():
            videoPath = os_path_join(Settings.getCustomPath(), normVideoName)
        else:
            log("getSoloVideo: Solo dir = %s" % videoPath)
            # Need to clean the path if we are going to store the file there
            # Handle stacked files that have a custom file name format
            if videoPath.startswith("stack://"):
                videoPath = videoPath.replace("stack://", "").split(" , ", 1)[0]
            # Need to remove the filename from the end  as we just want the directory
            # if not os.path.isdir(videoPath):
            fileExt = os.path.splitext(videoPath)[1]
            # If this is a file, then get it's parent directory
            if fileExt is not None and fileExt != "":
                videoPath = os.path.dirname(videoPath)

        log("getSoloVideo: videoPath = %s" % videoPath)

        # Now get the year and imdb number for the video
        year = xbmc.getInfoLabel("ListItem.Year")
        imdb = xbmc.getInfoLabel("ListItem.IMDBNumber")

        videoItem = {'title': normVideoName, 'path': videoPath, 'originalTitle': originalTitle, 'isTvShow': isTvShow, 'year': year, 'imdb': imdb}
        return videoItem

    # Checks if a theme exists in a directory
    def _doesThemeExist(self, directory):
        log("doesThemeExist: Checking directory: %s" % directory)
        # Check for custom theme directory
        if Settings.isThemeDirEnabled():
            themeDir = os_path_join(directory, Settings.getThemeDirectory())
            # Check if this directory exists
            if not dir_exists(themeDir):
                workingPath = directory
                # If the path currently ends in the directory separator
                # then we need to clear an extra one
                if (workingPath[-1] == os.sep) or (workingPath[-1] == os.altsep):
                    workingPath = workingPath[:-1]
                # If not check to see if we have a DVD VOB
                if (os_path_split(workingPath)[1] == 'VIDEO_TS') or (os_path_split(workingPath)[1] == 'BDMV'):
                    # Check the parent of the DVD Dir
                    themeDir = os_path_split(workingPath)[0]
                    themeDir = os_path_join(themeDir, Settings.getThemeDirectory())
            directory = themeDir

        # check if the directory exists before searching
        if dir_exists(directory):
            # Generate the regex
            themeFileRegEx = Settings.getThemeFileRegEx(audioOnly=True)

            dirs, files = list_dir(directory)
            for aFile in files:
                m = re.search(themeFileRegEx, aFile, re.IGNORECASE)
                if m:
                    log("doesThemeExist: Found match: " + aFile)
                    return True
        return False

    def _isTv(self):
        if xbmc.getCondVisibility("Container.Content(tvshows)"):
            return True
        if xbmc.getCondVisibility("Container.Content(Seasons)"):
            return True
        if xbmc.getCondVisibility("Container.Content(Episodes)"):
            return True
        if xbmc.getInfoLabel("container.folderpath") == "videodb://tvshows/titles/":
            return True  # TvShowTitles

        return False
